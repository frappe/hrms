// The boxed list, as the onboarding page draws it. Put BOX on the container and ROW on each child.
export const BOX = 'flex flex-col gap-px rounded-6 border border-outline-gray-1 p-2'

// A row you can click: the tile lights on hover and swallows the hairlines around it.
export const ROW =
  'relative flex w-full cursor-pointer items-center gap-3 rounded-4 px-3 py-2.5 text-left transition-colors before:pointer-events-none before:absolute before:inset-x-3 before:-top-px before:border-t before:border-outline-gray-1 first:before:hidden hover:bg-surface-gray-1 hover:before:opacity-0 [&:hover+*]:before:opacity-0'
