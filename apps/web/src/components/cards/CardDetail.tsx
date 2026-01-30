"use client";

import type { ApiCard } from "@trainerlab/shared-types";
import { CardImage } from "./CardImage";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface CardDetailProps {
  card: ApiCard;
  className?: string;
}

function StatRow({ label, value }: { label: string; value: React.ReactNode }) {
  if (!value) return null;
  return (
    <div className="flex justify-between py-1 border-b border-border/50 last:border-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

export function CardDetail({ card, className }: CardDetailProps) {
  const isLegalStandard = card.legalities?.standard === true;
  const isLegalExpanded = card.legalities?.expanded === true;

  return (
    <div className={cn("flex flex-col md:flex-row gap-8", className)}>
      {/* Card Image */}
      <div className="flex-shrink-0">
        <CardImage
          src={card.image_large}
          alt={card.name}
          size="large"
          priority
          className="mx-auto md:mx-0"
        />
      </div>

      {/* Card Details */}
      <div className="flex-1 space-y-6">
        {/* Header */}
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-3xl font-bold">{card.name}</h1>
            {card.hp && (
              <Badge variant="secondary" className="text-lg">
                {card.hp} HP
              </Badge>
            )}
          </div>
          {card.japanese_name && (
            <p className="text-muted-foreground">{card.japanese_name}</p>
          )}
          <div className="flex gap-2 mt-2">
            <Badge>{card.supertype}</Badge>
            {card.subtypes?.map((subtype) => (
              <Badge key={subtype} variant="outline">
                {subtype}
              </Badge>
            ))}
            {card.types?.map((type) => (
              <Badge key={type} variant="secondary">
                {type}
              </Badge>
            ))}
          </div>
        </div>

        {/* Abilities */}
        {card.abilities && card.abilities.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold mb-2">Abilities</h2>
            {card.abilities.map((ability, i) => (
              <div key={i} className="p-3 rounded-lg bg-muted/50 mb-2">
                <div className="font-medium text-primary">{ability.name}</div>
                {ability.type && (
                  <div className="text-xs text-muted-foreground">
                    {ability.type}
                  </div>
                )}
                {ability.effect && (
                  <p className="text-sm mt-1">{ability.effect}</p>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Attacks */}
        {card.attacks && card.attacks.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold mb-2">Attacks</h2>
            {card.attacks.map((attack, i) => (
              <div key={i} className="p-3 rounded-lg bg-muted/50 mb-2">
                <div className="flex justify-between items-center">
                  <div className="font-medium">{attack.name}</div>
                  {attack.damage && (
                    <div className="text-lg font-bold">{attack.damage}</div>
                  )}
                </div>
                {attack.cost && attack.cost.length > 0 && (
                  <div className="text-xs text-muted-foreground">
                    Cost: {attack.cost.join(", ")}
                  </div>
                )}
                {attack.effect && (
                  <p className="text-sm mt-1">{attack.effect}</p>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Stats */}
        <div>
          <h2 className="text-lg font-semibold mb-2">Details</h2>
          <div className="text-sm">
            <StatRow label="Set" value={card.set?.name || card.set_id} />
            <StatRow label="Number" value={card.number} />
            <StatRow label="Rarity" value={card.rarity} />
            <StatRow label="Evolves From" value={card.evolves_from} />
            {card.evolves_to && card.evolves_to.length > 0 && (
              <StatRow label="Evolves To" value={card.evolves_to.join(", ")} />
            )}
            <StatRow
              label="Retreat Cost"
              value={card.retreat_cost !== null ? card.retreat_cost : undefined}
            />
            {card.weaknesses && card.weaknesses.length > 0 && (
              <StatRow
                label="Weakness"
                value={card.weaknesses
                  .map((w) => `${w.type} ${w.value}`)
                  .join(", ")}
              />
            )}
            {card.resistances && card.resistances.length > 0 && (
              <StatRow
                label="Resistance"
                value={card.resistances
                  .map((r) => `${r.type} ${r.value}`)
                  .join(", ")}
              />
            )}
            <StatRow label="Regulation Mark" value={card.regulation_mark} />
          </div>
        </div>

        {/* Legality */}
        <div>
          <h2 className="text-lg font-semibold mb-2">Format Legality</h2>
          <div className="flex gap-2">
            <Badge variant={isLegalStandard ? "default" : "secondary"}>
              Standard: {isLegalStandard ? "Legal" : "Not Legal"}
            </Badge>
            <Badge variant={isLegalExpanded ? "default" : "secondary"}>
              Expanded: {isLegalExpanded ? "Legal" : "Not Legal"}
            </Badge>
          </div>
        </div>

        {/* Rules */}
        {card.rules && card.rules.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold mb-2">Rules</h2>
            <ul className="list-disc list-inside space-y-1 text-sm">
              {card.rules.map((rule, i) => (
                <li key={i}>{rule}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
