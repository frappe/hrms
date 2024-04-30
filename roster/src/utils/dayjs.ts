import dayjs from "dayjs";
import updateLocale from "dayjs/plugin/updateLocale";
import localizedFormat from "dayjs/plugin/localizedFormat";

dayjs.extend(updateLocale);
dayjs.extend(localizedFormat);

export default dayjs;
