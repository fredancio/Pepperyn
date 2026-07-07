'use client';

import { useState } from 'react';

const RPT_CSS = `
.rpt-wrap{background:#fff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
.rpt-hdr{background:linear-gradient(135deg,#1B73E8,#0D47A1);padding:14px 18px;display:flex;align-items:center;justify-content:space-between}
.rpt-badge{font-size:11px;font-weight:600;padding:3px 9px;background:rgba(255,255,255,.2);color:#fff;border-radius:6px;letter-spacing:.04em}
.rpt-conf-label{font-size:12px;color:#b8d2f8}
.rpt-body{padding:16px;display:flex;flex-direction:column;gap:14px}
.rpt-exec{border-left:4px solid #1B73E8;padding:8px 0 8px 14px}
.rpt-exec-title{font-size:11px;font-weight:700;color:#1B73E8;letter-spacing:.06em;margin-bottom:6px}
.rpt-exec-text{font-size:13px;line-height:1.65;color:#1A1A2E}
.rpt-exec-text b{font-weight:600}
.rpt-sec{border:1px solid #eef2fb;border-radius:12px;overflow:hidden}
.rpt-sec-hdr{display:flex;align-items:center;gap:8px;padding:11px 14px;cursor:pointer;user-select:none;background:#fff}
.rpt-sec-hdr:hover{background:#f8fbff}
.rpt-sec-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.rpt-sec-title{font-size:12px;font-weight:700;letter-spacing:.05em;color:#1A1A2E;flex:1}
.rpt-sec-count{font-size:11px;font-weight:600;padding:2px 7px;border-radius:10px;background:#eef2fb;color:#4a6fa5}
.rpt-chev{font-size:16px;color:#888;line-height:1;transition:transform .2s;display:inline-block}
.rpt-chev-open{transform:rotate(180deg)}
.rpt-sec-body{padding:12px;display:flex;flex-direction:column;gap:8px;border-top:1px solid #eef2fb}
.rpt-item{display:flex;align-items:flex-start;gap:10px;padding:11px 13px;border-radius:9px;font-size:13px;line-height:1.55;color:#1A1A2E}
.rpt-item b{font-weight:600}
.rpt-item-red{background:#fff5f5;border:1px solid #fde8e8}
.rpt-item-green{background:#f3fdf6;border:1px solid #d1f5de}
.rpt-item-amber{background:#fffbf0;border:1px solid #fde6a8}
.rpt-item-blue{background:#f0f6ff;border:1px solid #cce0fd}
.rpt-item-slate{background:#f7f9fb;border:1px solid #e6ecf3}
.rpt-item-icon{font-size:15px;flex-shrink:0;margin-top:1px}
.rpt-scores{display:flex;justify-content:space-around;padding:18px 8px 14px;border:1px solid #eef2fb;border-radius:12px}
.rpt-score-cell{display:flex;flex-direction:column;align-items:center;gap:5px}
.rpt-score-ring{width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:700;border-width:3.5px;border-style:solid}
.rpt-score-lbl{font-size:11px;color:#5F6368;text-align:center}
.rpt-conf-bar{display:flex;align-items:center;gap:8px;padding:6px 10px;border-radius:8px;font-size:11px;font-weight:600}
.rpt-conf-amber{background:#fffbf0;color:#a05c10;border:1px solid #fde6a8}
.rpt-conf-green{background:#f3fdf6;color:#1e7e4a;border:1px solid #d1f5de}
.rpt-conf-violet{background:#f5f3ff;color:#5b21b6;border:1px solid #ddd6fe}
.rpt-note{border-left:4px solid #1B73E8;background:#f0f6ff;padding:8px 12px;border-radius:0 8px 8px 0;font-size:12px;color:#1A1A2E;margin-top:2px}
.rpt-note-lbl{font-size:11px;font-weight:700;color:#1B73E8;margin-right:5px}
.rpt-note-violet{border-left-color:#7c3aed !important;background:#f5f3ff !important}
.rpt-note-violet .rpt-note-lbl{color:#5b21b6}
.rpt-risk-bdg{font-size:10px;font-weight:700;background:#fde8e8;color:#c0392b;padding:2px 6px;border-radius:4px;margin-right:5px;flex-shrink:0;margin-top:2px}
.rpt-bilan{display:flex;align-items:flex-start;gap:10px;padding:9px 13px;border-radius:9px;font-size:12.5px;color:#1A1A2E;background:#f5f3ff;border:1px solid #e0d9fd}
.rpt-bilan b{font-weight:600}
.rpt-decision{background:#EFF6FF;border:1px solid rgba(27,115,232,.25);border-radius:12px;padding:16px}
.rpt-decision-title{font-size:11px;font-weight:700;color:#1B73E8;letter-spacing:.06em;margin-bottom:7px}
.rpt-decision-text{font-size:13px;line-height:1.65;color:#1A1A2E}
.rpt-btns-row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}
.rpt-btn{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;padding:13px 6px;border-radius:12px;border:none;cursor:pointer;font-size:10.5px;font-weight:700;letter-spacing:.04em;line-height:1.3;text-align:center;color:#fff}
.rpt-btn-icon{font-size:17px}
.rpt-stakeholder{text-align:center;font-size:11.5px;color:#5F6368;padding:4px 0 2px;line-height:1.5}
.rpt-interactions{text-align:center;font-size:11px;color:#888;padding-top:2px}
`;

type SectionId = 'change' | 'alert' | 'prob' | 'opp' | 'plan' | 'margin' | 'cash' | 'bilan';

export function DeliverablesSection() {
  const [open, setOpen] = useState<Record<SectionId, boolean>>({
    change: true, alert: true, prob: true, opp: true, plan: true, margin: true, cash: true, bilan: true,
  });

  const toggle = (id: SectionId) => setOpen(p => ({ ...p, [id]: !p[id] }));

  const SecHdr = ({ id, dot, title, count }: { id: SectionId; dot: string; title: string; count?: number }) => (
    <div className="rpt-sec-hdr" onClick={() => toggle(id)}>
      <span className="rpt-sec-dot" style={{ background: dot }} />
      <span className="rpt-sec-title">{title}</span>
      {count !== undefined && <span className="rpt-sec-count">{count}</span>}
      <span className={`rpt-chev${open[id] ? ' rpt-chev-open' : ''}`}>˅</span>
    </div>
  );

  return (
    <section id="livrables" className="py-20 lg:py-28 bg-white border-t border-gray-100">
      <style dangerouslySetInnerHTML={{ __html: RPT_CSS }} />

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* ── Header ── */}
        <div className="text-center mb-14">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#1B73E8]/10 border border-[#1B73E8]/20 rounded-full mb-5">
            <span className="text-sm font-medium text-[#1B73E8]">Les livrables d&apos;une mission de conseil</span>
          </div>
          <h2 className="text-3xl lg:text-4xl font-extrabold text-[#1A1A2E] leading-tight max-w-2xl mx-auto">
            Ce que produit chaque analyse.
          </h2>
        </div>

        {/* ── Scrollable Report ── */}
        <div
          className="w-full rounded-2xl overflow-hidden"
          style={{
            maxHeight: 540,
            overflowY: 'auto',
            background: 'rgba(248,251,255,1)',
            border: '1.5px solid rgba(27,115,232,0.42)',
            boxShadow: [
              /* inset glass highlight — bord supérieur lumineux */
              'inset 0 1.5px 0 0 rgba(255,255,255,0.95)',
              /* reflet latéral gauche */
              'inset 1px 0 0 0 rgba(255,255,255,0.55)',
              /* halo extérieur de premier plan */
              '0 0 0 5px rgba(27,115,232,0.07)',
              /* ombre portée proche */
              '0 2px 8px rgba(0,0,0,0.08)',
              /* halo bleu intermédiaire */
              '0 10px 40px -6px rgba(27,115,232,0.26)',
              /* halo bleu profond */
              '0 28px 72px -16px rgba(27,115,232,0.20)',
            ].join(', '),
          }}
        >
          <div className="rpt-wrap">

            {/* Header bar */}
            <div className="rpt-hdr">
              <span className="rpt-badge">Résumé de l&apos;analyse</span>
              <span className="rpt-conf-label">Score de confiance : 94%</span>
            </div>

            <div className="rpt-body">

              {/* Executive summary */}
              <div className="rpt-exec">
                <div className="rpt-exec-title">📊 RÉSUMÉ EXÉCUTIF</div>
                <p className="rpt-exec-text">
                  <b>Situation</b> — Optilux réalise 8,2 M€ de CA sur 10 mois 2026, en hausse de +23% vs N-1, portée par son offre SaaS Enterprise (+31%) et l&apos;activation d&apos;un nouveau segment matériel.{' '}
                  <b>Problème</b> — La concentration client est critique (2 comptes = 61% du CA) et le délai moyen de paiement a dérivé à 78 jours, absorbant 312 K€ de trésorerie depuis janvier 2026.{' '}
                  <b>Action</b> — Lancer la procédure de diversification commerciale avant les renouvellements de mars 2027 et mettre en place un suivi DSO mensuel avec objectif 45 jours.
                </p>
              </div>

              {/* Ce qui a changé */}
              <div className="rpt-sec">
                <SecHdr id="change" dot="#FF6B35" title="🔁 CE QUI A CHANGÉ" count={3} />
                {open.change && (
                  <div className="rpt-sec-body">
                    <div className="rpt-item rpt-item-amber"><span className="rpt-item-icon">🔁</span><span><b>CA mensuel moyen en hausse</b> — de 680 K€ à 820 K€ (+20% en 6 mois) ; accélération confirmée en T3 2026 avec deux nouveaux contrats signés</span></div>
                    <div className="rpt-item rpt-item-amber"><span className="rpt-item-icon">🔁</span><span><b>BFR en dégradation structurelle</b> — +312 K€ depuis janvier 2026 malgré la croissance ; le cycle de trésorerie se détériore au rythme de la croissance</span></div>
                    <div className="rpt-item rpt-item-amber"><span className="rpt-item-icon">🔁</span><span><b>Nouveau segment &quot;ventes matériel&quot; activé en T3 2026</b> — 180 K€ générés en 4 mois sans force commerciale dédiée ; potentiel estimé à 500 K€/an si systématisé</span></div>
                  </div>
                )}
              </div>

              {/* Alertes */}
              <div className="rpt-sec">
                <SecHdr id="alert" dot="#FF6B35" title="⚠️ ALERTES" count={4} />
                {open.alert && (
                  <div className="rpt-sec-body">
                    <div className="rpt-item rpt-item-amber"><span className="rpt-item-icon">⚠️</span><span><b>Concentration client critique</b> — 2 clients représentent 61% du CA ; les renouvellements sont prévus en mars 2027, aucune garantie contractuelle au-delà</span></div>
                    <div className="rpt-item rpt-item-amber"><span className="rpt-item-icon">⚠️</span><span><b>DSO à 78 jours</b> — au-delà du seuil de vigilance sectoriel (45 j) ; chaque jour supplémentaire immobilise 27 K€ de trésorerie</span></div>
                    <div className="rpt-item rpt-item-amber"><span className="rpt-item-icon">⚠️</span><span><b>Masse salariale à 54% du CA</b> — en hausse de 18% YTD, absorbant 40% de la marge additionnelle générée par la croissance</span></div>
                    <div className="rpt-item rpt-item-amber"><span className="rpt-item-icon">⚠️</span><span><b>Module &quot;Support Premium&quot; en perte</b> — 48 K€ de revenus pour des coûts internes estimés à 65 K€ ; marge négative non provisionnée</span></div>
                  </div>
                )}
              </div>

              {/* Problèmes critiques */}
              <div className="rpt-sec">
                <SecHdr id="prob" dot="#DC2626" title="🔴 PROBLÈMES CRITIQUES" count={3} />
                {open.prob && (
                  <div className="rpt-sec-body">
                    <div className="rpt-item rpt-item-red"><span className="rpt-item-icon">🔴</span><span><b>Concentration client hors norme</b> — risque de décrochage de 60% du CA si un seul contrat n&apos;est pas renouvelé en mars 2027 ; aucun pipeline de remplacement identifié</span></div>
                    <div className="rpt-item rpt-item-red"><span className="rpt-item-icon">🔴</span><span><b>BFR hors de contrôle</b> — +312 K€ en 10 mois sans plan de réduction formalisé ; la croissance consomme davantage de trésorerie qu&apos;elle n&apos;en génère à court terme</span></div>
                    <div className="rpt-item rpt-item-red"><span className="rpt-item-icon">🔴</span><span><b>Dérive structurelle de la masse salariale</b> — 54% du CA vs norme sectorielle SaaS de 38–45% ; le levier opérationnel est annulé par l&apos;inflation des charges fixes RH</span></div>
                  </div>
                )}
              </div>

              {/* Opportunités */}
              <div className="rpt-sec">
                <SecHdr id="opp" dot="#2E7D32" title="🟢 OPPORTUNITÉS" count={4} />
                {open.opp && (
                  <div className="rpt-sec-body">
                    <div className="rpt-item rpt-item-green"><span className="rpt-item-icon">🟢</span><span><b>Upsell sur base installée</b> — 82 clients actifs, taux de pénétration module avancé à 31% ; passage à 55% représente un potentiel de +480 K€/an sans acquisition</span></div>
                    <div className="rpt-item rpt-item-green"><span className="rpt-item-icon">🟢</span><span><b>Expansion géographique BENELUX</b> — 0% de CA hors France actuellement ; 3 prospects qualifiés identifiés avec potentiel estimé à 900 K€ sur 18 mois</span></div>
                    <div className="rpt-item rpt-item-green"><span className="rpt-item-icon">🟢</span><span><b>Ventes matériel à systématiser</b> — 180 K€ en 4 mois sans effort commercial structuré ; une offre packagée logiciel + matériel pourrait générer 500 K€/an</span></div>
                    <div className="rpt-item rpt-item-green"><span className="rpt-item-icon">🟢</span><span><b>Réduction DSO</b> — passer de 78 à 45 jours libère ~450 K€ de trésorerie sans financement externe ; un simple processus de relance J+30 suffit</span></div>
                  </div>
                )}
              </div>

              {/* Plan d'action */}
              <div className="rpt-sec">
                <SecHdr id="plan" dot="#1B73E8" title="🎯 PLAN D'ACTION" count={4} />
                {open.plan && (
                  <div className="rpt-sec-body">
                    <div className="rpt-item rpt-item-blue"><span style={{ width: 16, height: 2, background: '#1B73E8', flexShrink: 0, marginTop: 10, display: 'block' }} /><span>Initier une procédure de qualification de 5 nouveaux comptes Enterprise avant le 31 janvier 2027 pour réduire la dépendance aux 2 clients critiques</span></div>
                    <div className="rpt-item rpt-item-blue"><span style={{ width: 16, height: 2, background: '#1B73E8', flexShrink: 0, marginTop: 10, display: 'block' }} /><span>Mettre en place un comité DSO mensuel avec relance automatique dès J+30 après émission de facture — objectif : 45 jours d&apos;ici fin T1 2027</span></div>
                    <div className="rpt-item rpt-item-blue"><span style={{ width: 16, height: 2, background: '#1B73E8', flexShrink: 0, marginTop: 10, display: 'block' }} /><span>Formaliser une offre packagée matériel + logiciel et former 2 commerciaux ; objectif 500 K€/an sur ce segment en 12 mois</span></div>
                    <div className="rpt-item rpt-item-blue"><span style={{ width: 16, height: 2, background: '#1B73E8', flexShrink: 0, marginTop: 10, display: 'block' }} /><span>Renégocier la structuration de la masse salariale avec un objectif de 48% du CA en mars 2027 — mix fixe/variable à ajuster dès les prochains recrutements</span></div>
                  </div>
                )}
              </div>

              {/* Scores */}
              <div className="rpt-scores">
                <div className="rpt-score-cell">
                  <div className="rpt-score-ring" style={{ borderColor: '#2E7D32', color: '#2E7D32' }}>8</div>
                  <span className="rpt-score-lbl">Rentabilité</span>
                </div>
                <div className="rpt-score-cell">
                  <div className="rpt-score-ring" style={{ borderColor: '#FF6B35', color: '#FF6B35' }}>6</div>
                  <span className="rpt-score-lbl">Risque</span>
                </div>
                <div className="rpt-score-cell">
                  <div className="rpt-score-ring" style={{ borderColor: '#2E7D32', color: '#2E7D32' }}>8</div>
                  <span className="rpt-score-lbl">Structure</span>
                </div>
              </div>

              {/* Margin Intelligence */}
              <div className="rpt-sec">
                <SecHdr id="margin" dot="#1B73E8" title="📊 MARGIN INTELLIGENCE" />
                {open.margin && (
                  <div className="rpt-sec-body">
                    <div className="rpt-conf-bar rpt-conf-green">Fiabilité données : 82% <span style={{ marginLeft: 6, opacity: .7 }}>· Données suffisantes</span></div>
                    <div className="rpt-item rpt-item-slate"><span>→ Marge brute : <b>71,4%</b> — charges variables directes bien identifiées (licences, sous-traitance technique)</span></div>
                    <div className="rpt-item rpt-item-slate"><span>→ Marge opérationnelle : <b>17,2%</b> — en baisse de 3,1 pts vs N-1 malgré la croissance ; dérive RH absorbant le levier</span></div>
                    <div className="rpt-item rpt-item-slate"><span>→ Marge nette : <b>11,8%</b> — solide en valeur absolue (967 K€) ; fragilisée par la dépendance à 2 clients</span></div>
                    <div className="rpt-item rpt-item-red"><span className="rpt-item-icon">🔴</span><span><b>Destruction marge</b> — dérive RH de +312 K€ YTD (+18%) absorbant 40% de la marge additionnelle issue de la croissance ; effet ciseau si le CA ralentit</span></div>
                    <div className="rpt-item rpt-item-green"><span className="rpt-item-icon">🟢</span><span><b>Création marge</b> — économies d&apos;échelle cloud confirmées (−8% de coût par client actif) ; potentiel de 95 K€ supplémentaires si la base clients triple d&apos;ici 2028</span></div>
                    <div className="rpt-item rpt-item-amber"><span className="rpt-item-icon">⚠️</span><span><b>Activité sous-performante</b> — module &quot;Support Premium&quot; : 48 K€ de revenus pour 65 K€ de coûts internes estimés. Marge négative non provisionnée à date.</span></div>
                    <div className="rpt-note"><span className="rpt-note-lbl">👉 En résumé :</span>La marge brute reste saine à 71%, mais la dérive RH érode la marge nette au rythme de la croissance. La priorité est de piloter le ratio charges/CA avec rigueur dès Q4 2026 avant d&apos;accélérer les recrutements.</div>
                  </div>
                )}
              </div>

              {/* Cash Forecast */}
              <div className="rpt-sec">
                <SecHdr id="cash" dot="#1B73E8" title="💰 CASH FORECAST & RISQUE LIQUIDITÉ" />
                {open.cash && (
                  <div className="rpt-sec-body">
                    <div className="rpt-conf-bar rpt-conf-amber">Fiabilité cash forecast : 68% <span style={{ marginLeft: 6, opacity: .7 }}>· Fiabilité partielle</span></div>
                    <p style={{ fontSize: 11, color: '#888', fontStyle: 'italic', padding: '2px 2px' }}>⚠️ Projection indicative — estimation basée sur les données disponibles.</p>
                    <div className="rpt-item rpt-item-slate"><span>→ <b>Projection 30 jours</b> — situation sous tension : encaissements prévus 420 K€ / décaissements 510 K€ (salaires + loyers + TVA) ; solde consommateur sur novembre 2026</span></div>
                    <div className="rpt-item rpt-item-slate"><span>→ <b>Projection 90 jours</b> — stabilisation possible si DSO revient à 55 jours ; sinon besoin de financement court terme estimé à 200–280 K€ (ligne de crédit à activer)</span></div>
                    <div className="rpt-item rpt-item-slate"><span>→ <b>DSO estimé</b> : 78 jours</span></div>
                    <div className="rpt-item rpt-item-slate"><span>→ <b>DPO estimé</b> : 42 jours</span></div>
                    <div className="rpt-item rpt-item-slate"><span>→ <b>BFR estimé</b> : 680 K€ (en hausse de +312 K€ depuis janvier 2026)</span></div>
                    <div className="rpt-item rpt-item-red" style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                      <span className="rpt-risk-bdg">⚠️ RISQUE</span>
                      <span>Pic de tension de trésorerie prévu entre le 15 et 28 novembre 2026 si le client principal (380 K€ de créances en cours) ne règle pas dans les délais annoncés</span>
                    </div>
                    <div style={{ marginTop: 2 }}>
                      <p style={{ fontSize: 11, fontWeight: 700, color: '#1A1A2E', marginBottom: 6 }}>📐 Indicateurs BFR</p>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                        <div className="rpt-item rpt-item-slate" style={{ padding: '7px 11px', fontSize: 12 }}>Raisons fiabilité : DSO absent des exports comptables, pas de tableau de flux, solde de trésorerie partiel — échéancier fournisseurs incomplet</div>
                        <div className="rpt-item rpt-item-slate" style={{ padding: '7px 11px', fontSize: 12 }}>→ DSO estimé : 78 jours</div>
                        <div className="rpt-item rpt-item-slate" style={{ padding: '7px 11px', fontSize: 12 }}>→ DPO estimé : 42 jours</div>
                        <div className="rpt-item rpt-item-slate" style={{ padding: '7px 11px', fontSize: 12 }}>→ BFR estimé : 680 000 €</div>
                      </div>
                    </div>
                    <div className="rpt-note"><span className="rpt-note-lbl">👉 En résumé :</span>La rentabilité est réelle mais la trésorerie est sous tension structurelle. Un DSO de 78 jours sur une croissance rapide crée un ciseau de financement qui devra être traité avant fin T4 2026, sous peine d&apos;avoir à recourir à un financement externe coûteux.</div>
                  </div>
                )}
              </div>

              {/* Bilan Intelligence */}
              <div className="rpt-sec">
                <SecHdr id="bilan" dot="#7c3aed" title="🏛️ BILAN INTELLIGENCE" />
                {open.bilan && (
                  <div className="rpt-sec-body">
                    <div className="rpt-conf-bar rpt-conf-violet">Fiabilité bilan : 78% <span style={{ marginLeft: 6, opacity: .7 }}>· Bilan disponible et exploitable</span></div>
                    <div className="rpt-bilan"><span>→ <b>Total Actif :</b> 2 840 000 €</span></div>
                    <div className="rpt-bilan"><span>→ <b>Actifs immobilisés :</b> 620 000 € <span style={{ color: '#6b7280', fontSize: 12 }}>(dont 480 K€ immobilisations incorporelles — capitalisation R&amp;D)</span></span></div>
                    <div className="rpt-bilan"><span>→ <b>Actifs circulants :</b> 2 220 000 €</span></div>
                    <div className="rpt-bilan"><span>→ <b>Créances clients :</b> <span style={{ color: '#b45309', fontWeight: 600 }}>1 680 000 €</span> <span style={{ color: '#6b7280', fontSize: 12 }}>(78j de CA — niveau préoccupant, représente 59% de l&apos;actif total)</span></span></div>
                    <div className="rpt-bilan"><span>→ <b>Trésorerie &amp; équivalents :</b> 340 000 €</span></div>
                    <div className="rpt-bilan"><span>→ <b>Capitaux propres :</b> <span style={{ color: '#15803d', fontWeight: 600 }}>1 240 000 €</span> <span style={{ color: '#6b7280', fontSize: 12 }}>(structure de financement saine)</span></span></div>
                    <div className="rpt-bilan"><span>→ <b>Dettes financières LT :</b> 480 000 € <span style={{ color: '#6b7280', fontSize: 12 }}>(emprunt bancaire 5 ans, échéance 2029)</span></span></div>
                    <div className="rpt-bilan"><span>→ <b>Dettes fournisseurs :</b> 210 000 €</span></div>
                    <div className="rpt-bilan"><span>→ <b>BFR structurel :</b> 1 470 000 € <span style={{ color: '#6b7280', fontSize: 12 }}>(Créances 1 680 K€ − Dettes frs 210 K€)</span></span></div>
                    <div className="rpt-bilan"><span>→ <b>Ratio d&apos;endettement :</b> <span style={{ color: '#15803d', fontWeight: 600 }}>0,39x</span> <span style={{ color: '#6b7280', fontSize: 12 }}>(dettes nettes 140 K€ / CP 1 240 K€ — niveau sain)</span></span></div>
                    <div className="rpt-note rpt-note-violet"><span className="rpt-note-lbl">👉 En résumé :</span>Bilan structurellement sain à 0,39x d&apos;endettement. L&apos;enjeu est concentré sur les créances clients (59% de l&apos;actif total) — le pilotage DSO est devenu l&apos;enjeu central de la santé financière à court terme.</div>
                  </div>
                )}
              </div>

              {/* Décision */}
              <div className="rpt-decision">
                <div className="rpt-decision-title">⚡ DÉCISION</div>
                <p className="rpt-decision-text">
                  Trois actions non négociables avant le 31 décembre 2026. Premièrement, réunion commerciale d&apos;urgence pour qualifier 5 prospects Enterprise et réduire la dépendance aux 2 clients critiques avant mars 2027. Deuxièmement, processus de relance DSO hebdomadaire — chaque jour gagné sur les 78 jours actuels libère 27 K€ de trésorerie ; l&apos;objectif de 45 jours en T1 2027 est atteignable sans investissement. Troisièmement, renégocier la structuration de la masse salariale (objectif 48% du CA) dès les prochains recrutements pour restaurer le levier opérationnel. La croissance est réelle, le bilan est sain, la structure tient — mais sans action immédiate sur le BFR et la concentration client, la trésorerie devient le plafond de verre de l&apos;accélération.
                </p>
              </div>

              {/* Export buttons */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div className="rpt-btns-row">
                  <button className="rpt-btn" style={{ backgroundColor: '#c0392b', color: '#ffffff' }}>
                    <span className="rpt-btn-icon">📄</span>EXECUTIVE REPORT
                  </button>
                  <button className="rpt-btn" style={{ backgroundColor: '#e07b2a', color: '#ffffff' }}>
                    <span className="rpt-btn-icon">📑</span>EXECUTIVE BOARD DECK
                  </button>
                  <button className="rpt-btn" style={{ backgroundColor: '#1B73E8', color: '#ffffff' }}>
                    <span className="rpt-btn-icon">📊</span>EXECUTIVE FINANCIAL MODEL
                  </button>
                </div>
                <p className="rpt-stakeholder">
                  <span style={{ color: '#1B73E8', fontWeight: 500 }}>Obtenez des rapports exécutifs plus détaillés</span> sous des formats adaptés à chaque partie prenante — dirigeants, CFO, banques, conseils...
                </p>
              </div>

              <p className="rpt-interactions">Interactions contextuelles restantes : 3/3</p>

            </div>
          </div>
        </div>

        {/* Scroll hint removed */}

        {/* Bridge dots */}
        <div className="relative w-full mt-8 mb-8">
          <div className="absolute top-3.5 left-[16.66%] right-[16.66%] h-px opacity-20" style={{ background: 'linear-gradient(90deg,#c0392b 0%,#c0392b 33.3%,#e07b2a 33.3%,#e07b2a 66.6%,#1B73E8 66.6%,#1B73E8 100%)' }} />
          <div className="grid grid-cols-3 relative z-10">
            {[
              { color: '#c0392b', icon: <><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></> },
              { color: '#e07b2a', icon: <><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></> },
              { color: '#1B73E8', icon: <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/> },
            ].map(({ color, icon }, i) => (
              <div key={i} className="flex justify-center">
                <div className="w-7 h-7 rounded-full border-2 bg-white flex items-center justify-center" style={{ borderColor: color, color }}>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" aria-hidden="true">{icon}</svg>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ── 3 cards ── */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">

          {/* Card 1 — Executive Report (red) */}
          <div className="relative bg-white rounded-2xl p-6 flex flex-col gap-4 overflow-hidden" style={{ border: '1.5px solid #e8d0ce', boxShadow: '0 0 0 3px rgba(192,57,43,0.04), 0 8px 28px -4px rgba(192,57,43,0.12), 0 2px 8px rgba(0,0,0,0.05)' }}>
            <div className="absolute top-0 left-0 right-0 h-0.5 bg-[#c0392b]" />
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider bg-[#fff0ef] text-[#c0392b]">ÉTAPE 1 · COMPRENDRE</span>
            <h3 className="text-[15px] font-bold text-[#c0392b] leading-snug">Executive Report</h3>
            <div className="h-px bg-gray-100" />
            <div><p className="text-[9.5px] font-bold uppercase tracking-widest text-[#b0bec5] mb-1">Pourquoi ce livrable existe</p><p className="text-xs text-[#2d3748] leading-relaxed">Un diagnostic financier complet et priorisé — ce qui crée et ce qui détruit de la valeur, avec les décisions à prendre dans l&apos;ordre. <span className="font-semibold text-[#1A1A2E]">Le point de départ de toute action.</span></p></div>
            <div><p className="text-[9.5px] font-bold uppercase tracking-widest text-[#b0bec5] mb-1">À quelle décision il sert</p><p className="text-xs text-[#2d3748] leading-relaxed">Répondre à : <span className="font-semibold text-[#1A1A2E]">que se passe-t-il réellement, et que faut-il faire en premier ?</span> Sans ce diagnostic, toute action est aveugle.</p></div>
            <div><p className="text-[9.5px] font-bold uppercase tracking-widest text-[#b0bec5] mb-1">Pour qui</p><p className="text-xs text-[#2d3748] leading-relaxed">Le dirigeant, le DAF — toute personne qui pilote l&apos;entreprise et doit décider vite, sur des faits.</p></div>
            <div><p className="text-[9.5px] font-bold uppercase tracking-widest text-[#b0bec5] mb-1">À quel moment</p><p className="text-xs font-semibold text-[#c0392b]">Dès l&apos;import de vos données, en quelques minutes.</p></div>
          </div>

          {/* Card 2 — Executive Board Deck (orange) */}
          <div className="relative bg-white rounded-2xl p-6 flex flex-col gap-4 overflow-hidden" style={{ border: '1.5px solid #e8d5be', boxShadow: '0 0 0 3px rgba(224,123,42,0.04), 0 8px 28px -4px rgba(224,123,42,0.12), 0 2px 8px rgba(0,0,0,0.05)' }}>
            <div className="absolute top-0 left-0 right-0 h-0.5 bg-[#e07b2a]" />
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider bg-[#fff3e8] text-[#c06010]">ÉTAPE 2 · COMMUNIQUER</span>
            <h3 className="text-[15px] font-bold text-[#e07b2a] leading-snug">Executive Board Deck</h3>
            <div className="h-px bg-gray-100" />
            <div><p className="text-[9.5px] font-bold uppercase tracking-widest text-[#b0bec5] mb-1">Pourquoi ce livrable existe</p><p className="text-xs text-[#2d3748] leading-relaxed">Une synthèse exécutive prête à présenter — les conclusions du rapport traduites en slides clairs, <span className="font-semibold text-[#1A1A2E]">sans retravail ni mise en forme supplémentaire.</span></p></div>
            <div><p className="text-[9.5px] font-bold uppercase tracking-widest text-[#b0bec5] mb-1">À quelle décision il sert</p><p className="text-xs text-[#2d3748] leading-relaxed">Aligner le Comité de Direction sur les priorités <span className="font-semibold text-[#1A1A2E]">en réunion plutôt que par email.</span> La décision se prend dans la salle, pas après.</p></div>
            <div><p className="text-[9.5px] font-bold uppercase tracking-widest text-[#b0bec5] mb-1">Pour qui</p><p className="text-xs text-[#2d3748] leading-relaxed">Le Comité de Direction, le conseil d&apos;administration, les investisseurs — toute audience qui décide collectivement.</p></div>
            <div><p className="text-[9.5px] font-bold uppercase tracking-widest text-[#b0bec5] mb-1">À quel moment</p><p className="text-xs font-semibold text-[#e07b2a]">Avant chaque comité de direction.</p></div>
          </div>

          {/* Card 3 — Executive Financial Model (blue) */}
          <div className="relative bg-white rounded-2xl p-6 flex flex-col gap-4 overflow-hidden" style={{ border: '1.5px solid #b8cfee', boxShadow: '0 0 0 3px rgba(27,115,232,0.04), 0 8px 28px -4px rgba(27,115,232,0.12), 0 2px 8px rgba(0,0,0,0.05)' }}>
            <div className="absolute top-0 left-0 right-0 h-0.5 bg-[#1B73E8]" />
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider bg-[#e8f0fe] text-[#1557b0]">ÉTAPE 3 · MODÉLISER</span>
            <h3 className="text-[15px] font-bold text-[#1B73E8] leading-snug">Executive Financial Model</h3>
            <div className="h-px bg-gray-100" />
            <div><p className="text-[9.5px] font-bold uppercase tracking-widest text-[#b0bec5] mb-1">Pourquoi ce livrable existe</p><p className="text-xs text-[#2d3748] leading-relaxed">Un outil dynamique de modélisation et de simulation — pour <span className="font-semibold text-[#1A1A2E]">mesurer l&apos;impact de chaque décision, tester des scénarios</span> et construire des projections chiffrées sur 12 à 36 mois.</p></div>
            <div><p className="text-[9.5px] font-bold uppercase tracking-widest text-[#b0bec5] mb-1">À quelle décision il sert</p><p className="text-xs text-[#2d3748] leading-relaxed">Répondre à : <span className="font-semibold text-[#1A1A2E]">&quot;si je fais X, que se passe-t-il ?&quot;</span> Chaque levier est simulé, chaque scénario est vérifiable. Sert de fondation à tout dossier bancaire ou stratégique.</p></div>
            <div><p className="text-[9.5px] font-bold uppercase tracking-widest text-[#b0bec5] mb-1">Pour qui</p><p className="text-xs text-[#2d3748] leading-relaxed">Le DAF, la banque, l&apos;investisseur — toute partie prenante qui a besoin de projections fiables pour valider une décision.</p></div>
            <div><p className="text-[9.5px] font-bold uppercase tracking-widest text-[#b0bec5] mb-1">À quel moment</p><p className="text-xs font-semibold text-[#1B73E8]">En amont de toute décision stratégique ou levée de fonds.</p></div>
          </div>

        </div>
      </div>
    </section>
  );
}
