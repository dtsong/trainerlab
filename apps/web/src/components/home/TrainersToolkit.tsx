"use client";

import { ExternalLink, Wrench } from "lucide-react";
import { SectionLabel } from "@/components/ui/section-label";

interface ToolkitLink {
  name: string;
  description: string;
  href: string;
}

const toolkitLinks: ToolkitLink[] = [
  {
    name: "Limitless TCG",
    description: "Tournament results and decklists database",
    href: "https://limitlesstcg.com",
  },
  {
    name: "PTCGO / PTCGL",
    description: "Official Pokemon Trading Card Game Online",
    href: "https://www.pokemon.com/us/pokemon-tcg/play-online/",
  },
  {
    name: "Pokemon TCG Subreddit",
    description: "Community discussions and deck help",
    href: "https://www.reddit.com/r/pkmntcg/",
  },
  {
    name: "PokemonCard.io",
    description: "Card prices and collection tracking",
    href: "https://pokemoncard.io",
  },
];

export function TrainersToolkit() {
  return (
    <section className="bg-slate-50 py-12 md:py-16">
      <div className="container">
        <SectionLabel
          label="Trainer's Toolkit"
          icon={<Wrench className="h-4 w-4" />}
          className="mb-8"
        />

        <p className="mb-6 max-w-2xl text-slate-600">
          Essential community resources for competitive Pokemon TCG players.
        </p>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {toolkitLinks.map((link) => (
            <a
              key={link.name}
              href={link.href}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-start gap-3 rounded-lg border border-slate-200 bg-white p-4 transition-all hover:border-teal-200 hover:shadow-md"
            >
              <div className="flex-1">
                <h3 className="font-medium text-slate-900 group-hover:text-teal-600 transition-colors">
                  {link.name}
                </h3>
                <p className="mt-1 text-sm text-slate-500">
                  {link.description}
                </p>
              </div>
              <ExternalLink className="h-4 w-4 flex-shrink-0 text-slate-400 group-hover:text-teal-500 transition-colors" />
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}
