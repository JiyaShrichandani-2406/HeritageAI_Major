export default function PageHeader({ eyebrow, title, subtitle, actions, breadcrumb }) {
  return (
    <div className="container-page pt-8 pb-6">
      {breadcrumb && <div className="text-xs text-ink-500 mb-3">{breadcrumb}</div>}
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          {eyebrow && <div className="eyebrow">{eyebrow}</div>}
          <h1 className="font-heading text-3xl md:text-5xl font-bold leading-tight mt-2">{title}</h1>
          {subtitle && <p className="mt-3 text-ink-500 max-w-2xl">{subtitle}</p>}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
    </div>
  );
}
