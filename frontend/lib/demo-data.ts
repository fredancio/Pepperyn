/**
 * Données de démonstration — External User Testing Prototype (2026-08-05).
 *
 * Jeu de données 100% fictif, gelé, généré une seule fois via les vraies
 * fonctions produit (ArcService.build_portfolio_briefing /
 * build_review_briefing, backend/services/arc_service.py) sur un
 * Supabase mocké — pas une liste triée à la main. Script jetable, non
 * versionné : /tmp/portfolio-validation/build_demo_dataset.py.
 *
 * Réutilise exactement le jeu de données à 12 clients déjà validé dans
 * docs/Product/PORTFOLIO_HOME_PRODUCT_VALIDATION.md (Mission 1) :
 *   - plusieurs priorités (urgent, to_check, done) ;
 *   - deux clients à égalité stricte de priorité et d'ancienneté (Nguyen,
 *     Girard — 60 jours, urgent) ;
 *   - clients à un seul point actif (Nguyen, Girard, Vidal, Fontaine,
 *     Belhadj, Roussel) et à plusieurs points actifs (Lefèvre ×4, Martin
 *     ×3, Lemoine ×2, Dupuis ×2) ;
 *   - âges variés (4 à 92 jours) ;
 *   - why_it_matters affiché (Martin, Roussel) et volontairement masqué
 *     (les autres) ;
 *   - titre court (Nguyen) et titre long (Fontaine) ;
 *   - Traiteur Second (e11) : uniquement un point "closed" — ne doit
 *     JAMAIS apparaître dans le Portfolio (règle du correctif Closed-Only
 *     Clients), mais reste consultable comme historique dans son Review
 *     Briefing direct ;
 *   - Cabinet Rousseau (e12) : aucun arc — ne doit JAMAIS apparaître.
 *
 * Noms et sociétés entièrement inventés — aucune réutilisation de données
 * réelles, aucune donnée des anciens dossiers Optilux/Démo.
 */

import type { PortfolioCard, BriefingItem } from '@/lib/types';

export interface DemoEntity {
  id: string;
  name: string;
}

export const DEMO_ENTITIES: DemoEntity[] = [
  {
    "id": "e1",
    "name": "Cabinet Lefèvre & Associés"
  },
  {
    "id": "e2",
    "name": "Atelier Nguyen"
  },
  {
    "id": "e3",
    "name": "Boulangerie Girard"
  },
  {
    "id": "e4",
    "name": "Pharmacie Vidal"
  },
  {
    "id": "e5",
    "name": "Cabinet Lemoine"
  },
  {
    "id": "e6",
    "name": "SCI Fontaine"
  },
  {
    "id": "e7",
    "name": "Atelier Martin"
  },
  {
    "id": "e8",
    "name": "Restaurant Belhadj"
  },
  {
    "id": "e9",
    "name": "Cabinet Dupuis"
  },
  {
    "id": "e10",
    "name": "Menuiserie Roussel"
  },
  {
    "id": "e11",
    "name": "Traiteur Second"
  },
  {
    "id": "e12",
    "name": "Cabinet Rousseau"
  }
];

/** Cartes Portfolio — sortie gelée de build_portfolio_briefing(). 10 cartes (Rousseau et Traiteur Second exclus par construction). */
export const DEMO_PORTFOLIO_CARDS: PortfolioCard[] = [
  {
    "entity_id": "e1",
    "entity_name": "Cabinet Lefèvre & Associés",
    "top_item": {
      "arc_id": "l1",
      "source_type": "decision_arc",
      "entity_id": "e1",
      "title": "Renégocier le contrat cadre avec le fournisseur principal",
      "learning_text": null,
      "priority": "urgent",
      "temporal_context": "Recommandé il y a 92 jours",
      "why_it_matters": "Toujours sans décision confirmée après au moins une revue.",
      "questions_to_ask": [
        "Où en êtes-vous sur cette recommandation ?",
        "Souhaitez-vous l'appliquer, ou faut-il la reconsidérer ?"
      ],
      "age_days": 92
    },
    "other_active_count": 3,
    "why_it_matters_display": null
  },
  {
    "entity_id": "e2",
    "entity_name": "Atelier Nguyen",
    "top_item": {
      "arc_id": "n1",
      "source_type": "decision_arc",
      "entity_id": "e2",
      "title": "Statuer sur l'embauche d'un second artisan",
      "learning_text": null,
      "priority": "urgent",
      "temporal_context": "Recommandé il y a 60 jours",
      "why_it_matters": "Toujours sans décision confirmée après au moins une revue.",
      "questions_to_ask": [
        "Où en êtes-vous sur cette recommandation ?",
        "Souhaitez-vous l'appliquer, ou faut-il la reconsidérer ?"
      ],
      "age_days": 60
    },
    "other_active_count": 0,
    "why_it_matters_display": null
  },
  {
    "entity_id": "e3",
    "entity_name": "Boulangerie Girard",
    "top_item": {
      "arc_id": "g1",
      "source_type": "decision_arc",
      "entity_id": "e3",
      "title": "Renouveler le bail commercial du point de vente",
      "learning_text": null,
      "priority": "urgent",
      "temporal_context": "Recommandé il y a 60 jours",
      "why_it_matters": "Toujours sans décision confirmée après au moins une revue.",
      "questions_to_ask": [
        "Où en êtes-vous sur cette recommandation ?",
        "Souhaitez-vous l'appliquer, ou faut-il la reconsidérer ?"
      ],
      "age_days": 60
    },
    "other_active_count": 0,
    "why_it_matters_display": null
  },
  {
    "entity_id": "e4",
    "entity_name": "Pharmacie Vidal",
    "top_item": {
      "arc_id": "v1",
      "source_type": "decision_arc",
      "entity_id": "e4",
      "title": "Décider du rachat de l'officine voisine",
      "learning_text": null,
      "priority": "urgent",
      "temporal_context": "Recommandé il y a 45 jours",
      "why_it_matters": "Toujours sans décision confirmée après au moins une revue.",
      "questions_to_ask": [
        "Où en êtes-vous sur cette recommandation ?",
        "Souhaitez-vous l'appliquer, ou faut-il la reconsidérer ?"
      ],
      "age_days": 45
    },
    "other_active_count": 0,
    "why_it_matters_display": null
  },
  {
    "entity_id": "e5",
    "entity_name": "Cabinet Lemoine",
    "top_item": {
      "arc_id": "le1",
      "source_type": "decision_arc",
      "entity_id": "e5",
      "title": "Réviser la grille tarifaire des prestations",
      "learning_text": null,
      "priority": "urgent",
      "temporal_context": "Recommandé il y a 38 jours",
      "why_it_matters": "Toujours sans décision confirmée après au moins une revue.",
      "questions_to_ask": [
        "Où en êtes-vous sur cette recommandation ?",
        "Souhaitez-vous l'appliquer, ou faut-il la reconsidérer ?"
      ],
      "age_days": 38
    },
    "other_active_count": 1,
    "why_it_matters_display": null
  },
  {
    "entity_id": "e6",
    "entity_name": "SCI Fontaine",
    "top_item": {
      "arc_id": "f1",
      "source_type": "decision_arc",
      "entity_id": "e6",
      "title": "Renégocier les conditions du bail commercial du site principal avant l'échéance du préavis contractuel de six mois",
      "learning_text": null,
      "priority": "to_check",
      "temporal_context": "Décidé il y a 25 jours",
      "why_it_matters": "Exécution en cours.",
      "questions_to_ask": [
        "Où en est l'exécution depuis notre dernier échange ?"
      ],
      "age_days": 25
    },
    "other_active_count": 0,
    "why_it_matters_display": null
  },
  {
    "entity_id": "e7",
    "entity_name": "Atelier Martin",
    "top_item": {
      "arc_id": "m1",
      "source_type": "decision_arc",
      "entity_id": "e7",
      "title": "Investissement dans une nouvelle machine-outil",
      "learning_text": null,
      "priority": "to_check",
      "temporal_context": "Exécuté il y a 12 jours",
      "why_it_matters": "Effet pas encore confirmé dans une analyse.",
      "questions_to_ask": [
        "Quel effet avez-vous observé depuis ?"
      ],
      "age_days": 12
    },
    "other_active_count": 2,
    "why_it_matters_display": "Effet pas encore confirmé dans une analyse."
  },
  {
    "entity_id": "e8",
    "entity_name": "Restaurant Belhadj",
    "top_item": {
      "arc_id": "b1",
      "source_type": "decision_arc",
      "entity_id": "e8",
      "title": "Ajuster la carte suite à la hausse du coût des matières premières",
      "learning_text": null,
      "priority": "to_check",
      "temporal_context": "Recommandé il y a 5 jours",
      "why_it_matters": "Décision encore en attente.",
      "questions_to_ask": [
        "Qu'avez-vous décidé pour cette recommandation ?"
      ],
      "age_days": 5
    },
    "other_active_count": 0,
    "why_it_matters_display": null
  },
  {
    "entity_id": "e9",
    "entity_name": "Cabinet Dupuis",
    "top_item": {
      "arc_id": "d2",
      "source_type": "decision_arc",
      "entity_id": "e9",
      "title": "Étudier l'ouverture d'une deuxième agence",
      "learning_text": null,
      "priority": "to_check",
      "temporal_context": "Recommandé il y a 4 jours",
      "why_it_matters": "Décision encore en attente.",
      "questions_to_ask": [
        "Qu'avez-vous décidé pour cette recommandation ?"
      ],
      "age_days": 4
    },
    "other_active_count": 1,
    "why_it_matters_display": null
  },
  {
    "entity_id": "e10",
    "entity_name": "Menuiserie Roussel",
    "top_item": {
      "arc_id": "r1",
      "source_type": "decision_arc",
      "entity_id": "e10",
      "title": "Confirmer l'effet du changement de fournisseur de bois",
      "learning_text": null,
      "priority": "done",
      "temporal_context": "Effet confirmé il y a 8 jours",
      "why_it_matters": "Apprentissage en attente.",
      "questions_to_ask": [
        "Cet effet s'est-il maintenu depuis ?"
      ],
      "age_days": 8
    },
    "other_active_count": 0,
    "why_it_matters_display": "Apprentissage en attente."
  }
];

/** Briefings complets par client (historique "closed" inclus) — sortie gelée de build_review_briefing(entity_id=...). */
export const DEMO_REVIEW_BRIEFINGS: Record<string, BriefingItem[]> = {
  "e1": [
    {
      "arc_id": "l1",
      "source_type": "decision_arc",
      "entity_id": "e1",
      "title": "Renégocier le contrat cadre avec le fournisseur principal",
      "learning_text": null,
      "priority": "urgent",
      "temporal_context": "Recommandé il y a 92 jours",
      "why_it_matters": "Toujours sans décision confirmée après au moins une revue.",
      "questions_to_ask": [
        "Où en êtes-vous sur cette recommandation ?",
        "Souhaitez-vous l'appliquer, ou faut-il la reconsidérer ?"
      ],
      "age_days": 92
    },
    {
      "arc_id": "l2",
      "source_type": "decision_arc",
      "entity_id": "e1",
      "title": "Suivre la mise en place du nouveau logiciel de paie",
      "learning_text": null,
      "priority": "to_check",
      "temporal_context": "Décidé il y a 10 jours",
      "why_it_matters": "Exécution en cours.",
      "questions_to_ask": [
        "Où en est l'exécution depuis notre dernier échange ?"
      ],
      "age_days": 10
    },
    {
      "arc_id": "l3",
      "source_type": "decision_arc",
      "entity_id": "e1",
      "title": "Vérifier l'effet de la renégociation bancaire",
      "learning_text": null,
      "priority": "to_check",
      "temporal_context": "Exécuté il y a 5 jours",
      "why_it_matters": "Effet pas encore confirmé dans une analyse.",
      "questions_to_ask": [
        "Quel effet avez-vous observé depuis ?"
      ],
      "age_days": 5
    },
    {
      "arc_id": "l4",
      "source_type": "decision_arc",
      "entity_id": "e1",
      "title": "Confirmer l'apprentissage sur le changement d'expert-comptable",
      "learning_text": null,
      "priority": "done",
      "temporal_context": "Effet confirmé il y a 3 jours",
      "why_it_matters": "Apprentissage en attente.",
      "questions_to_ask": [
        "Cet effet s'est-il maintenu depuis ?"
      ],
      "age_days": 3
    }
  ],
  "e2": [
    {
      "arc_id": "n1",
      "source_type": "decision_arc",
      "entity_id": "e2",
      "title": "Statuer sur l'embauche d'un second artisan",
      "learning_text": null,
      "priority": "urgent",
      "temporal_context": "Recommandé il y a 60 jours",
      "why_it_matters": "Toujours sans décision confirmée après au moins une revue.",
      "questions_to_ask": [
        "Où en êtes-vous sur cette recommandation ?",
        "Souhaitez-vous l'appliquer, ou faut-il la reconsidérer ?"
      ],
      "age_days": 60
    }
  ],
  "e3": [
    {
      "arc_id": "g1",
      "source_type": "decision_arc",
      "entity_id": "e3",
      "title": "Renouveler le bail commercial du point de vente",
      "learning_text": null,
      "priority": "urgent",
      "temporal_context": "Recommandé il y a 60 jours",
      "why_it_matters": "Toujours sans décision confirmée après au moins une revue.",
      "questions_to_ask": [
        "Où en êtes-vous sur cette recommandation ?",
        "Souhaitez-vous l'appliquer, ou faut-il la reconsidérer ?"
      ],
      "age_days": 60
    }
  ],
  "e4": [
    {
      "arc_id": "v1",
      "source_type": "decision_arc",
      "entity_id": "e4",
      "title": "Décider du rachat de l'officine voisine",
      "learning_text": null,
      "priority": "urgent",
      "temporal_context": "Recommandé il y a 45 jours",
      "why_it_matters": "Toujours sans décision confirmée après au moins une revue.",
      "questions_to_ask": [
        "Où en êtes-vous sur cette recommandation ?",
        "Souhaitez-vous l'appliquer, ou faut-il la reconsidérer ?"
      ],
      "age_days": 45
    }
  ],
  "e5": [
    {
      "arc_id": "le1",
      "source_type": "decision_arc",
      "entity_id": "e5",
      "title": "Réviser la grille tarifaire des prestations",
      "learning_text": null,
      "priority": "urgent",
      "temporal_context": "Recommandé il y a 38 jours",
      "why_it_matters": "Toujours sans décision confirmée après au moins une revue.",
      "questions_to_ask": [
        "Où en êtes-vous sur cette recommandation ?",
        "Souhaitez-vous l'appliquer, ou faut-il la reconsidérer ?"
      ],
      "age_days": 38
    },
    {
      "arc_id": "le2",
      "source_type": "decision_arc",
      "entity_id": "e5",
      "title": "Suivre l'intégration du nouveau collaborateur",
      "learning_text": null,
      "priority": "to_check",
      "temporal_context": "Décidé il y a 6 jours",
      "why_it_matters": "Exécution en cours.",
      "questions_to_ask": [
        "Où en est l'exécution depuis notre dernier échange ?"
      ],
      "age_days": 6
    }
  ],
  "e6": [
    {
      "arc_id": "f1",
      "source_type": "decision_arc",
      "entity_id": "e6",
      "title": "Renégocier les conditions du bail commercial du site principal avant l'échéance du préavis contractuel de six mois",
      "learning_text": null,
      "priority": "to_check",
      "temporal_context": "Décidé il y a 25 jours",
      "why_it_matters": "Exécution en cours.",
      "questions_to_ask": [
        "Où en est l'exécution depuis notre dernier échange ?"
      ],
      "age_days": 25
    }
  ],
  "e7": [
    {
      "arc_id": "m1",
      "source_type": "decision_arc",
      "entity_id": "e7",
      "title": "Investissement dans une nouvelle machine-outil",
      "learning_text": null,
      "priority": "to_check",
      "temporal_context": "Exécuté il y a 12 jours",
      "why_it_matters": "Effet pas encore confirmé dans une analyse.",
      "questions_to_ask": [
        "Quel effet avez-vous observé depuis ?"
      ],
      "age_days": 12
    },
    {
      "arc_id": "m2",
      "source_type": "decision_arc",
      "entity_id": "e7",
      "title": "Suivre la négociation avec le nouveau fournisseur de matières premières",
      "learning_text": null,
      "priority": "to_check",
      "temporal_context": "Décidé il y a 8 jours",
      "why_it_matters": "Exécution en cours.",
      "questions_to_ask": [
        "Où en est l'exécution depuis notre dernier échange ?"
      ],
      "age_days": 8
    },
    {
      "arc_id": "m3",
      "source_type": "decision_arc",
      "entity_id": "e7",
      "title": "Étudier le passage à la facturation électronique",
      "learning_text": null,
      "priority": "to_check",
      "temporal_context": "Recommandé il y a 5 jours",
      "why_it_matters": "Décision encore en attente.",
      "questions_to_ask": [
        "Qu'avez-vous décidé pour cette recommandation ?"
      ],
      "age_days": 5
    }
  ],
  "e8": [
    {
      "arc_id": "b1",
      "source_type": "decision_arc",
      "entity_id": "e8",
      "title": "Ajuster la carte suite à la hausse du coût des matières premières",
      "learning_text": null,
      "priority": "to_check",
      "temporal_context": "Recommandé il y a 5 jours",
      "why_it_matters": "Décision encore en attente.",
      "questions_to_ask": [
        "Qu'avez-vous décidé pour cette recommandation ?"
      ],
      "age_days": 5
    }
  ],
  "e9": [
    {
      "arc_id": "d2",
      "source_type": "decision_arc",
      "entity_id": "e9",
      "title": "Étudier l'ouverture d'une deuxième agence",
      "learning_text": null,
      "priority": "to_check",
      "temporal_context": "Recommandé il y a 4 jours",
      "why_it_matters": "Décision encore en attente.",
      "questions_to_ask": [
        "Qu'avez-vous décidé pour cette recommandation ?"
      ],
      "age_days": 4
    },
    {
      "arc_id": "d1",
      "source_type": "decision_arc",
      "entity_id": "e9",
      "title": "Valider l'apprentissage sur la réduction des délais de paiement clients",
      "learning_text": null,
      "priority": "done",
      "temporal_context": "Effet confirmé il y a 15 jours",
      "why_it_matters": "Apprentissage en attente.",
      "questions_to_ask": [
        "Cet effet s'est-il maintenu depuis ?"
      ],
      "age_days": 15
    }
  ],
  "e10": [
    {
      "arc_id": "r1",
      "source_type": "decision_arc",
      "entity_id": "e10",
      "title": "Confirmer l'effet du changement de fournisseur de bois",
      "learning_text": null,
      "priority": "done",
      "temporal_context": "Effet confirmé il y a 8 jours",
      "why_it_matters": "Apprentissage en attente.",
      "questions_to_ask": [
        "Cet effet s'est-il maintenu depuis ?"
      ],
      "age_days": 8
    }
  ],
  "e11": [
    {
      "arc_id": "s1",
      "source_type": "decision_arc",
      "entity_id": "e11",
      "title": "Clôturer le dossier de refinancement du véhicule utilitaire",
      "learning_text": "Le refinancement a été finalisé sans impact sur la trésorerie court terme.",
      "priority": "closed",
      "temporal_context": "Clôturé le 16 juillet 2026",
      "why_it_matters": null,
      "questions_to_ask": [],
      "age_days": 20
    }
  ],
  "e12": []
};

export function getDemoPortfolio(): PortfolioCard[] {
  return DEMO_PORTFOLIO_CARDS;
}

export function getDemoReviewBriefing(entityId?: string): BriefingItem[] {
  if (!entityId) {
    // Sans filtre : concatène tous les items actifs (hors closed), comme le
    // ferait build_review_briefing(entity_id=None) côté backend.
    return Object.values(DEMO_REVIEW_BRIEFINGS)
      .flat()
      .filter((item) => item.priority !== 'closed');
  }
  return DEMO_REVIEW_BRIEFINGS[entityId] || [];
}

export function getDemoEntityName(entityId: string): string | undefined {
  return DEMO_ENTITIES.find((e) => e.id === entityId)?.name;
}
