type TimelineItem = { time: string; text: string; emphasis?: boolean; footnote?: string };

const before: TimelineItem[] = [
  { time: 'Lundi', text: 'Le dirigeant découvre un problème.' },
  { time: 'Mardi', text: 'On demande des analyses.' },
  { time: 'Mercredi', text: 'Excel circule.' },
  { time: 'Jeudi', text: 'Le PowerPoint est préparé.' },
  { time: 'Vendredi', text: 'Le CODIR décide.', emphasis: true, footnote: 'Trop tard.' },
];

const after: TimelineItem[] = [
  { time: 'Lundi 8h30', text: 'Import des données.' },
  { time: '8h33', text: 'Rapport exécutif.' },
  { time: '8h35', text: 'Board Deck.' },
  { time: '8h36', text: 'Décisions priorisées.' },
  { time: '9h00', text: 'Le Comité de Direction décide.', emphasis: true },
];

function Timeline({ items, tone }: { items: TimelineItem[]; tone: 'before' | 'after' }) {
  const isAfter = tone === 'after';
  return (
    <div className="flex flex-col gap-0">
      {items.map((item, i) => (
        <div key={item.time} className="flex gap-4">
          {/* Rail */}
          <div className="flex flex-col items-center flex-shrink-0">
            <span
              className={`w-2.5 h-2.5 rounded-full mt-1.5 ${
                item.emphasis ? (isAfter ? 'bg-[#1B73E8]' : 'bg-red-400') : 'bg-gray-300'
              }`}
            />
            {i < items.length - 1 && <span className="w-px flex-1 bg-gray-200 my-1" />}
          </div>
          {/* Content */}
          <div className={`pb-8 ${i === items.length - 1 ? 'pb-0' : ''}`}>
            <p className={`text-xs font-bold uppercase tracking-wide ${isAfter ? 'text-[#1B73E8]' : 'text-[#5F6368]'}`}>
              {item.time}
            </p>
            <p className={`text-base mt-0.5 ${item.emphasis ? 'font-bold text-[#1A1A2E]' : 'text-[#1A1A2E]'}`}>
              {item.text}
            </p>
            {'footnote' in item && item.footnote && (
              <p className="text-sm font-bold text-red-500 mt-1">{item.footnote}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export function StorytellingSection() {
  return (
    <section className="py-20 lg:py-28 bg-white border-t border-gray-100">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">

        <div className="text-center mb-14">
          <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E] leading-tight">
            Une semaine avant Pepperyn.
          </h2>
        </div>

        <div className="grid md:grid-cols-2 gap-10 md:gap-16">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-[#5F6368] mb-6">Sans Pepperyn</p>
            <Timeline items={before} tone="before" />
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-[#1B73E8] mb-6">Une semaine avec Pepperyn</p>
            <Timeline items={after} tone="after" />
          </div>
        </div>

      </div>
    </section>
  );
}
