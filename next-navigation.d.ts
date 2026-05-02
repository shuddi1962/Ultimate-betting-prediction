declare module 'next/navigation' {
  export function useParams(): { [key: string]: string }
  export function useRouter(): { push: (url: string) => void }
}
