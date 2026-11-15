from collections import Counter, defaultdict

import frappe
from frappe import _
from frappe.utils import add_days, date_diff, get_quarter_start, get_year_start, getdate, nowdate

PERIODS = ("last_30_days", "last_90_days", "this_quarter", "this_year")
STAGES = ("Applied", "Shortlisted", "Interviewing", "Offered", "Hired")
OPENINGS_SHOWN = 10
# fewer records than this before the period make a percent change noise
COMPARISON_FLOOR = 10
# the categorical chart ramp has 10 colours; past that the tail sums into one series
SOURCES_SHOWN = 10
# an applicant without a source was entered by hand in desk
NO_SOURCE = "Added by HR"
OFFER_LABELS = {"Accepted": "Accepted", "Rejected": "Declined", "Awaiting Response": "Awaiting reply"}
INTERVIEW_LABELS = {
	"Cleared": "Cleared",
	"Rejected": "Rejected",
	"Pending": "Pending",
	"Under Review": "Under review",
	"Cancelled": "Cancelled",
}


@frappe.whitelist(methods=["GET"])
def get_recruitment_dashboard(period: str = "last_90_days") -> dict:
	frappe.has_permission("Job Applicant", "read", throw=True)
	if period not in PERIODS:
		frappe.throw(_("Unknown period: {0}").format(period))
	return RecruitmentDashboard(period).get_data()


class RecruitmentDashboard:
	"""Hiring numbers for applicants created in a period, up to today."""

	def __init__(self, period: str, to_date=None):
		self.to_date = getdate(to_date or nowdate())
		self.from_date = get_period_start(period, self.to_date)
		self.days = date_diff(self.to_date, self.from_date) + 1
		self.openings = get_open_openings()
		self.labels = get_opening_labels(self.openings)
		self.applicants = get_applicants(self.from_date, self.to_date)
		names = [applicant.name for applicant in self.applicants]
		self.interviews = get_linked("Interview", names, ["job_applicant", "status"])
		self.offers = get_linked("Job Offer", names, ["job_applicant", "status", "offer_date", "docstatus"])
		self.interviewed = {
			interview.job_applicant for interview in self.interviews if interview.status != "Cancelled"
		}
		# Draft and Ready to Send offers haven't reached the candidate yet
		self.offers = [offer for offer in self.offers if offer.status in OFFER_LABELS]
		self.offered = {offer.job_applicant for offer in self.offers}

	def get_data(self) -> dict:
		return {
			"first_use": is_first_use(),
			"days": self.days,
			"period": {"from": str(self.from_date), "to": str(self.to_date)},
			"open_roles": len(self.openings),
			"positions": sum(opening.vacancies or 0 for opening in self.openings),
			"hired": sum(applicant.stage == "Hired" for applicant in self.applicants),
			"applications": len(self.applicants),
			"applications_delta": self.get_applications_delta(),
			"time_to_hire": self.get_time_to_hire(),
			"not_reviewed": self.get_not_reviewed(),
			"openings": self.get_openings_chart(),
			"funnel": self.get_funnel(),
			"weekly": self.get_weekly_sources(),
			"sources": self.get_hires_by_source(),
			"source_filters": self.get_source_filters(),
			"offers": self.get_offers_made(),
			"interviews": self.get_interviews_held(),
		}

	def get_applications_delta(self) -> int | None:
		"""Percent change against the period of equal length just before, when that had enough to compare."""
		previous_start = add_days(self.from_date, -self.days)
		previous = frappe.get_list(
			"Job Applicant",
			filters=[["creation", ">=", previous_start], ["creation", "<", self.from_date]],
			fields=[{"COUNT": "*"}],
			as_list=True,
		)[0][0]
		if previous < COMPARISON_FLOOR:
			return None
		return round((len(self.applicants) - previous) * 100 / previous)

	def get_time_to_hire(self) -> dict | None:
		"""Days from application to the accepted offer's date; stage changes carry no dates.

		An offer dated before the application was backdated, so it says nothing about speed."""
		created = {applicant.name: applicant.creation for applicant in self.applicants}
		hired = {applicant.name for applicant in self.applicants if applicant.stage == "Hired"}
		days = [
			date_diff(offer.offer_date, created[offer.job_applicant])
			for offer in self.offers
			if offer.job_applicant in hired
			and offer.docstatus == 1
			and offer.status == "Accepted"
			and offer.offer_date
			and getdate(offer.offer_date) >= getdate(created[offer.job_applicant])
		]
		if not days:
			return None
		return {"days": round(sum(days) / len(days)), "hires": len(days)}

	def get_not_reviewed(self) -> dict:
		waiting = [
			applicant.creation
			for applicant in self.applicants
			if applicant.stage == "Applied" and applicant.status != "Hold"
		]
		oldest = date_diff(self.to_date, min(waiting)) if waiting else None
		return {"count": len(waiting), "oldest_days": oldest}

	def get_openings_chart(self) -> dict:
		"""Applicants per open opening by current stage; rejected ones are left out."""
		stages = defaultdict(Counter)
		for applicant in self.applicants:
			stages[applicant.job_title][applicant.stage] += 1

		openings = self.openings
		if len(openings) > OPENINGS_SHOWN:
			by_applicants = sorted(openings, key=lambda opening: -stages[opening.name].total())
			openings = by_applicants[:OPENINGS_SHOWN]

		rows = [
			{"opening": opening.name, **get_opening_row(self.labels[opening.name], stages[opening.name])}
			for opening in openings
		]
		rows.sort(key=lambda row: -row["total"])
		return {"rows": rows, "total": len(self.openings), "attention": self.get_attention()}

	def get_attention(self) -> list[dict]:
		"""Open openings past their closing date, then those nobody has applied to yet."""
		names = [opening.name for opening in self.openings]
		applied = set(
			frappe.get_list("Job Applicant", {"job_title": ["in", names]}, pluck="job_title", distinct=True)
		)
		rows = []
		for opening in self.openings:
			close_days = date_diff(opening.closes_on, self.to_date) if opening.closes_on else None
			if close_days is not None and close_days < 0:
				rows.append(
					{"title": self.labels[opening.name], "reason": "past_closing", "days": -close_days}
				)
			elif opening.name not in applied:
				rows.append(
					{"title": self.labels[opening.name], "reason": "no_applicants", "close_days": close_days}
				)
		return sorted(rows, key=get_attention_order)

	def get_funnel(self) -> list[dict]:
		"""How many applicants reached each stage or a later one, so the funnel never widens."""
		hired = {applicant.name for applicant in self.applicants if applicant.stage == "Hired"}
		offered = self.offered | hired
		interviewing = self.interviewed | offered
		shortlisted = {
			applicant.name for applicant in self.applicants if applicant.stage in STAGES[1:]
		} | interviewing
		reached = {
			"Applied": len(self.applicants),
			"Shortlisted": len(shortlisted),
			"Interviewing": len(interviewing),
			"Offered": len(offered),
			"Hired": len(hired),
		}
		return [{"stage": stage, "count": reached[stage]} for stage in STAGES]

	def get_weekly_sources(self) -> dict:
		"""Applications per week (weeks start on Monday), split by source."""
		totals = Counter(get_source(applicant) for applicant in self.applicants)
		sources = [source for source, _count in sorted(totals.items(), key=lambda item: (-item[1], item[0]))]
		shown = sources if len(sources) <= SOURCES_SHOWN else sources[: SOURCES_SHOWN - 1]
		other = _("Other")

		weeks = defaultdict(Counter)
		for applicant in self.applicants:
			source = get_source(applicant)
			weeks[get_week_start(applicant.creation)][source if source in shown else other] += 1

		if len(shown) < len(sources):
			shown = [*shown, other]
		rows = []
		week = get_week_start(self.from_date)
		while week <= self.to_date:
			# the first and last weeks are cut at the period's edges
			bounds = {"from": str(max(week, self.from_date)), "to": str(min(add_days(week, 6), self.to_date))}
			rows.append({"week": str(week), **bounds, **{source: weeks[week][source] for source in shown}})
			week = add_days(week, 7)
		return {"sources": shown, "rows": rows}

	def get_hires_by_source(self) -> list[dict]:
		"""Per source: applicants who only applied, who were interviewed, and who were hired."""
		rows = defaultdict(Counter)
		for applicant in self.applicants:
			if applicant.stage == "Hired":
				outcome = "Hired"
			elif applicant.name in self.interviewed:
				outcome = "Interviewed"
			else:
				outcome = "Applied only"
			rows[get_source(applicant)][outcome] += 1

		result = [
			{"source": source, **{key: counts[key] for key in ("Applied only", "Interviewed", "Hired")}}
			for source, counts in rows.items()
		]
		return sorted(result, key=lambda row: (-sum(rows[row["source"]].values()), row["source"]))

	def get_source_filters(self) -> dict:
		"""The list filter that finds each source's applicants. A source no single filter can find is left out."""
		blank = any(not applicant.source for applicant in self.applicants)
		named = any(applicant.source == NO_SOURCE for applicant in self.applicants)
		filters = {}
		for source in {get_source(applicant) for applicant in self.applicants}:
			if source != NO_SOURCE:
				filters[source] = ["=", source]
			elif not (blank and named):
				filters[source] = ["is", "not set"] if blank else ["=", source]
		return filters

	def get_offers_made(self) -> list[dict]:
		"""Sent offers dated in the period, whenever their applicant applied."""
		statuses = frappe.get_list(
			"Job Offer",
			filters={
				"docstatus": 1,
				"status": ["in", list(OFFER_LABELS)],
				"offer_date": ["between", [self.from_date, self.to_date]],
			},
			pluck="status",
		)
		return count_labels(statuses, OFFER_LABELS)

	def get_interviews_held(self) -> list[dict]:
		"""Interviews scheduled in the period, whenever their applicant applied."""
		statuses = frappe.get_list(
			"Interview",
			filters={"docstatus": ["!=", 2], "scheduled_on": ["between", [self.from_date, self.to_date]]},
			pluck="status",
		)
		return count_labels(statuses, INTERVIEW_LABELS)


def get_period_start(period: str, to_date):
	if period == "last_30_days":
		return add_days(to_date, -29)
	if period == "last_90_days":
		return add_days(to_date, -89)
	if period == "this_quarter":
		return get_quarter_start(to_date)
	return get_year_start(to_date)


def get_open_openings() -> list[dict]:
	return frappe.get_list(
		"Job Opening",
		filters={"status": "Open"},
		fields=["name", "job_title", "location", "vacancies", "closes_on"],
		order_by="creation asc",
	)


def get_applicants(from_date, to_date) -> list[dict]:
	return frappe.get_list(
		"Job Applicant",
		filters=[["creation", ">=", from_date], ["creation", "<", add_days(to_date, 1)]],
		fields=["name", "job_title", "stage", "status", "source", "creation"],
		order_by="creation asc",
	)


def get_linked(doctype: str, applicants: list[str], fields: list[str]) -> list[dict]:
	"""Live (not cancelled) records of a doctype that point at the given applicants."""
	if not applicants:
		return []
	return frappe.get_list(
		doctype,
		filters={"job_applicant": ["in", applicants], "docstatus": ["<", 2]},
		fields=fields,
	)


def is_first_use() -> bool:
	return not frappe.db.count("Job Opening") and not frappe.db.count("Job Applicant")


def get_opening_labels(openings: list[dict]) -> dict[str, str]:
	"""Opening titles, with the location (or ID) added where two openings share a title."""
	titles = Counter(opening.job_title for opening in openings)
	return {
		opening.name: opening.job_title
		if titles[opening.job_title] == 1
		else f"{opening.job_title} ({opening.location or opening.name})"
		for opening in openings
	}


def get_opening_row(label: str, stages: Counter) -> dict:
	counts = {stage: stages[stage] for stage in STAGES}
	return {"role": label, **counts, "total": sum(counts.values())}


def get_attention_order(row: dict) -> tuple:
	if row["reason"] == "past_closing":
		return (0, -row["days"])
	close_days = row["close_days"]
	return (1, close_days is None, close_days or 0)


def count_labels(statuses: list[str], labels: dict[str, str]) -> list[dict]:
	counts = Counter(statuses)
	return [{"name": label, "status": status, "count": counts[status]} for status, label in labels.items()]


def get_source(applicant: dict) -> str:
	return applicant.source or NO_SOURCE


def get_week_start(value):
	day = getdate(value)
	return add_days(day, -day.weekday())
