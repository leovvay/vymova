import type { ReactNode } from "react";

interface PageHeadProps {
  title: ReactNode;
  lead?: ReactNode;
  aside?: ReactNode;
}

export function PageHead({ title, lead, aside }: PageHeadProps) {
  return (
    <header className="page-head">
      <div className="page-head__main">
        <h1 className="page-head__title">{title}</h1>
        {lead && <p className="page-head__lead">{lead}</p>}
      </div>
      {aside && <div className="page-head__aside">{aside}</div>}
    </header>
  );
}
