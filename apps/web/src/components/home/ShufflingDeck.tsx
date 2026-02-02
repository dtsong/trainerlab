"use client";

import { useEffect, useState } from "react";

interface CardProps {
  index: number;
  isShuffling: boolean;
  shufflePhase: number;
  totalCards: number;
}

function Card({ index, isShuffling, shufflePhase, totalCards }: CardProps) {
  // Calculate base position in the stack
  const baseOffset = index * 2;
  const baseRotation = (index - totalCards / 2) * 0.5;

  // Determine if this card moves during current shuffle phase
  const movesInPhase1 = index % 2 === 0;
  const movesInPhase2 = index % 2 === 1;

  // Calculate animation transforms based on shuffle state
  let transform = `translateY(${-baseOffset}px) rotate(${baseRotation}deg)`;
  let zIndex = index;
  let transition = "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)";

  if (isShuffling) {
    if (shufflePhase === 1 && movesInPhase1) {
      // First set of cards lift and move right
      transform = `translateY(${-baseOffset - 40}px) translateX(20px) rotate(${baseRotation + 5}deg)`;
      zIndex = totalCards + index;
    } else if (shufflePhase === 2 && movesInPhase1) {
      // First set drops back with new position
      const newIndex = Math.floor(index / 2);
      transform = `translateY(${-newIndex * 2}px) rotate(${(newIndex - totalCards / 4) * 0.5}deg)`;
      zIndex = newIndex;
    } else if (shufflePhase === 3 && movesInPhase2) {
      // Second set lifts and moves left
      transform = `translateY(${-baseOffset - 35}px) translateX(-15px) rotate(${baseRotation - 4}deg)`;
      zIndex = totalCards + index;
    } else if (shufflePhase === 4) {
      // All cards settle into new random-ish positions
      const shuffledIndex = (index * 7 + 3) % totalCards;
      transform = `translateY(${-shuffledIndex * 2}px) rotate(${(shuffledIndex - totalCards / 2) * 0.5}deg)`;
      zIndex = shuffledIndex;
    }
  }

  return (
    <div
      className="absolute bottom-0 left-1/2 -translate-x-1/2 w-12 h-16 rounded-md shadow-md border border-slate-300 overflow-hidden"
      style={{
        transform,
        zIndex,
        transition,
        background:
          "linear-gradient(180deg, #dc2626 0%, #dc2626 45%, #1f2937 45%, #1f2937 55%, #f5f5f4 55%, #f5f5f4 100%)",
      }}
    >
      {/* Card sleeve texture overlay */}
      <div className="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_50%_50%,transparent_30%,black_70%)]" />

      {/* Pokeball design */}
      <svg
        viewBox="0 0 48 64"
        className="absolute inset-0 w-full h-full"
        preserveAspectRatio="xMidYMid meet"
      >
        {/* Center band (dark) */}
        <rect x="0" y="28" width="48" height="8" fill="#1f2937" />

        {/* Center circle - outer ring */}
        <circle
          cx="24"
          cy="32"
          r="8"
          fill="#f5f5f4"
          stroke="#1f2937"
          strokeWidth="2"
        />

        {/* Center circle - inner */}
        <circle cx="24" cy="32" r="4" fill="#1f2937" />

        {/* Center dot */}
        <circle cx="24" cy="32" r="2" fill="#f5f5f4" />

        {/* Subtle shine on top half */}
        <ellipse cx="18" cy="18" rx="6" ry="4" fill="white" opacity="0.3" />
      </svg>
    </div>
  );
}

export function ShufflingDeck() {
  const [isShuffling, setIsShuffling] = useState(false);
  const [shufflePhase, setShufflePhase] = useState(0);
  const totalCards = 8;

  useEffect(() => {
    // Start shuffle cycle every 6 seconds
    const shuffleInterval = setInterval(() => {
      setIsShuffling(true);
      setShufflePhase(1);

      // Phase 2 after 300ms
      setTimeout(() => setShufflePhase(2), 300);
      // Phase 3 after 600ms
      setTimeout(() => setShufflePhase(3), 600);
      // Phase 4 after 900ms
      setTimeout(() => setShufflePhase(4), 900);
      // Reset after 1200ms
      setTimeout(() => {
        setIsShuffling(false);
        setShufflePhase(0);
      }, 1200);
    }, 6000);

    // Initial shuffle after 2 seconds
    const initialTimeout = setTimeout(() => {
      setIsShuffling(true);
      setShufflePhase(1);
      setTimeout(() => setShufflePhase(2), 300);
      setTimeout(() => setShufflePhase(3), 600);
      setTimeout(() => setShufflePhase(4), 900);
      setTimeout(() => {
        setIsShuffling(false);
        setShufflePhase(0);
      }, 1200);
    }, 2000);

    return () => {
      clearInterval(shuffleInterval);
      clearTimeout(initialTimeout);
    };
  }, []);

  return (
    <div className="relative w-20 h-24">
      {/* Shadow under deck */}
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-14 h-2 bg-ink-black/10 rounded-full blur-sm" />

      {/* Cards */}
      {Array.from({ length: totalCards }).map((_, index) => (
        <Card
          key={index}
          index={index}
          isShuffling={isShuffling}
          shufflePhase={shufflePhase}
          totalCards={totalCards}
        />
      ))}

      {/* Label */}
      <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 whitespace-nowrap">
        <span className="font-mono text-[10px] uppercase tracking-wide text-pencil/60">
          Live Data
        </span>
      </div>
    </div>
  );
}
