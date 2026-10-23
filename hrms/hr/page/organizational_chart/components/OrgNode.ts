import { defineComponent, h, inject } from 'vue'
import { Avatar } from 'frappe-ui'

declare const __: (text: string, args?: unknown[]) => string

// Recursive by design: a render function can call itself, an SFC cannot register itself.
// A node is a face, a name and a role. Everything else opens in the person sheet.
//
// Layout: a team where nobody manages anyone is drawn as a STACK under its manager; teams
// that branch again are drawn as a ROW, because there the shape carries information.
const OrgNode = defineComponent({
  name: 'OrgNode',
  props: { id: { type: String, required: true } },
  setup(props) {
    const org: any = inject('org')
    return () => {
      const p = org.byId.value[props.id]
      const kids = org.reportsOf(props.id)
      const open = org.expanded.value.has(props.id)
      const picked = org.selected.value === props.id
      const isYou = org.you.value === props.id
      const wide = org.orientation.value === 'horizontal'
      // Left to right, every team is one column, so only top to bottom needs the stack.
      const stack = !wide && kids.length > 0 && kids.every((k: any) => !org.reportsOf(k.id).length)

      const card = h(
        'button',
        {
          'data-node': props.id,
          type: 'button',
          class: [
            'flex w-52 items-center gap-2.5 rounded-5 px-3 py-2.5 text-left shadow-sm transition-colors',
            picked ? 'bg-surface-gray-2' : 'bg-surface-elevation-1 hover:bg-surface-gray-1',
          ],
          'aria-pressed': picked ? 'true' : 'false',
          onClick: () => org.select(props.id),
        },
        [
          h('span', { class: 'relative flex shrink-0' }, [
            h(Avatar, { image: p.photo, label: p.name, size: 'lg' }),
            p.out
              ? h('span', { class: 'absolute -bottom-0.5 -right-0.5 rounded-full bg-surface-base p-0.5', title: p.away, 'aria-label': p.away }, [
                  h('span', { class: 'block size-2 rounded-full bg-surface-blue-5' }),
                ])
              : null,
          ]),
          h('span', { class: 'min-w-0 flex-1' }, [
            h('span', { class: 'flex items-center gap-1.5' }, [
              h('span', { class: 'truncate text-base text-ink-gray-8' }, p.name),
              isYou ? h('span', { class: 'shrink-0 text-sm text-ink-gray-5' }, __('You')) : null,
            ]),
            h('span', { class: 'block truncate text-sm text-ink-gray-5' }, p.role),
          ]),
        ],
      )

      // Hangs below the card. Closed, it previews who is underneath: faces and a count.
      const pill = kids.length
        ? h(
            'button',
            {
              type: 'button',
              class: [
                wide ? 'absolute left-full top-1/2 z-10 -ml-1.5 -translate-y-1/2' : 'absolute left-1/2 top-full z-10 -mt-1.5 -translate-x-1/2',
                'flex h-6 items-center gap-1.5 rounded-4 border border-outline-gray-2 bg-surface-base text-sm text-ink-gray-7 transition-colors hover:bg-surface-gray-2',
                open ? 'px-1' : 'group pl-1 pr-1',
              ],
              'aria-expanded': open ? 'true' : 'false',
              'aria-label': open ? __('Hide {0}\'s team', [p.name]) : __('Show {0}\'s team, {1} people', [p.name, kids.length]),
              onClick: (e: Event) => {
                e.stopPropagation()
                org.toggle(props.id)
              },
            },
            open
              ? [h('span', { class: `${wide ? 'lucide-chevron-left' : 'lucide-chevron-up'} size-3.5 text-ink-gray-6`, 'aria-hidden': 'true' })]
              : [
                  h(
                    'span',
                    { class: 'flex -space-x-1.5' },
                    kids.slice(0, 3).map((k: any) =>
                      h('span', { key: k.id, class: 'relative flex rounded-full bg-surface-base p-0.5 transition-colors group-hover:bg-surface-gray-2' }, [h(Avatar, { image: k.photo, label: k.name, size: 'xs' })]),
                    ),
                  ),
                  h('span', { class: 'tabular-nums' }, String(kids.length)),
                  h('span', { class: `${wide ? 'lucide-chevron-right' : 'lucide-chevron-down'} size-3.5 text-ink-gray-6`, 'aria-hidden': 'true' }),
                ],
          )
        : null

      // Connectors are borders, so an elbow can be one element with a real rounded corner.
      const line = (cls: string) => h('span', { class: `pointer-events-none absolute border-outline-gray-3 ${cls}`, 'aria-hidden': 'true' })
      const n = kids.length

      let children = null
      if (open && n && wide) {
        // One column to the right; each report joins a spine with an elbow.
        const joins = (i: number) =>
          n === 1
            ? [line('left-0 top-1/2 w-8 border-t')]
            : i === 0
              ? [line('left-0 top-1/2 bottom-0 w-8 rounded-tl-[12px] border-l border-t')]
              : i === n - 1
                ? [line('left-0 top-0 bottom-[calc(50%_-_1px)] w-8 rounded-bl-[12px] border-l border-b')]
                : [line('inset-y-0 left-0 border-l'), line('left-0 top-1/2 w-8 border-t')]
        children = h('div', { class: 'relative flex flex-col justify-center pl-12' }, [
          line('left-0 top-1/2 w-12 border-t'),
          ...kids.map((k: any, i: number) =>
            h('div', { key: k.id, class: 'relative py-1.5 pl-8' }, [...joins(i), h(OrgNode, { id: k.id })]),
          ),
        ])
      } else if (open && n && stack) {
        children = h('div', { class: 'relative flex w-64 flex-col gap-2 pl-12 pt-8' }, [
          line('left-9 top-0 bottom-[40px] border-l'),
          ...kids.map((k: any, i: number) =>
            h('div', { key: k.id, class: 'relative' }, [
              i === n - 1
                ? line('-left-3 top-[calc(50%_-_11px)] h-3 w-3 rounded-bl-[12px] border-b border-l')
                : line('-left-3 top-1/2 w-3 border-t'),
              h(OrgNode, { id: k.id }),
            ]),
          ),
        ])
      } else if (open && n) {
        const joins = (i: number) =>
          n === 1
            ? [line('left-1/2 top-0 h-8 border-l')]
            : i === 0
              ? [line('left-1/2 right-0 top-0 h-8 rounded-tl-[12px] border-l border-t')]
              : i === n - 1
                ? [line('left-0 right-[calc(50%_-_1px)] top-0 h-8 rounded-tr-[12px] border-r border-t')]
                : [line('inset-x-0 top-0 border-t'), line('left-1/2 top-0 h-8 border-l')]
        children = h('div', { class: 'relative flex items-start pt-8' }, [
          line('left-1/2 top-0 h-8 border-l'),
          ...kids.map((k: any, i: number) =>
            h('div', { key: k.id, class: 'relative px-2.5 pt-8' }, [...joins(i), h(OrgNode, { id: k.id })]),
          ),
        ])
      }

      return h('div', { class: wide ? 'flex items-center' : 'flex flex-col items-center' }, [h('div', { class: 'relative' }, [card, pill]), children])
    }
  },
})

export default OrgNode
