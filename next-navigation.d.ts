declare module 'next/link' {
  import React from 'react';
  export interface LinkProps {
    href: string;
    as?: string;
    replace?: boolean;
    scroll?: boolean;
    shallow?: boolean;
    passHref?: boolean;
    prefetch?: boolean;
    locale?: string | false;
    legacyBehavior?: boolean;
    children: React.ReactNode;
  }
  export default function Link(props: LinkProps): JSX.Element;
}

declare module 'next/navigation' {
  export function useParams(): { [key: string]: string };
  export function useRouter(): { push: (url: string) => void };
}

declare module 'next/dist/lib/metadata/types/metadata-interface.js' {
  export type ResolvingMetadata = any;
  export type ResolvingViewport = any;
}
