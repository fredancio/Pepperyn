const steps = [
  'Suivi mensuel.',
  'Comparaison des analyses.',
  'Mesure des décisions réellement prises.',
  'Détection automatique des nouvelles dérives.',
  'Nouvelles priorités.',
  'Mémoire financière.',
];

export function CopilotSection() {
  return (
    <section className="py-20 lg:py-28 bg-[#0A2540]">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">

        <div className="text-center mb-14">
          <h2 className="text-3xl lg:text-4xl font-extrabold text-white leading-tight max-w-xl mx-auto">
            Le rapport n&apos;est que le début.
          </h2>
        </div>

        <div className="flex flex-col gap-6 mb-14">
          <p className="text-sm font-bold uppercase tracking-widest text-blue-300 text-center">Aujourd&apos;hui</p>
          <p className="text-lg text-blue-100 text-center max-w-2xl mx-auto leading-relaxed">
            La plupart des logiciels s&apos;arrêtent après l&apos;analyse.
            <br />
            <span className="text-white font-semibold">Pepperyn continue.</span>
          </p>
        </div>

        {/* Chaîne d'accompagnement */}
        <div className="flex flex-col gap-0 max-w-md mx-auto">
          {steps.map((step, i) => (
            <div key={step} className="flex gap-4">
              <div className="flex flex-col items-center flex-shrink-0">
                <span className="w-2 h-2 rounded-full bg-[#60A5FA] mt-2" />
                {i < steps.length - 1 && <span className="w-px flex-1 bg-white/10 my-1" />}
              </div>
              <p className={`pb-6 text-base ${i === steps.length - 1 ? 'text-white font-bold' : 'text-blue-100'}`}>
                {step}
              </p>
            </div>
          ))}
        </div>

        <p className="text-center text-sm text-blue-300 mt-4 max-w-md mx-auto">
          Pepperyn ne vend pas un rapport. Il vend un accompagnement.
        </p>

      </div>
    </section>
  );
}
