import { clsx, type ClassValue } from "clsx"
import { extendTailwindMerge } from "tailwind-merge"

export const customTwMerge = extendTailwindMerge({
    extend: {
        classGroups: {
            'font-family': ['font-mono', 'font-sans']
        }
    }
})

export function cn(...inputs: ClassValue[]) {
  return customTwMerge(clsx(inputs))
}
