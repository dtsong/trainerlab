import { ImageResponse } from "next/og";

import { humanizeSlug, parseOgPath, type OgImageDescriptor } from "../utils";

export const runtime = "edge";

const OG_SIZE = {
  width: 1200,
  height: 630,
};

function getSubtitle(descriptor: OgImageDescriptor): string {
  if (descriptor.type === "widget") return "Embeddable Creator Widget";
  if (descriptor.type === "lab-note") return "Lab Notes";
  if (descriptor.type === "evolution") return "Evolution Analysis";
  if (descriptor.type === "archetype") return "Archetype Report";
  return "Live Meta Snapshot";
}

function getTitle(descriptor: OgImageDescriptor): string {
  if (descriptor.type === "widget") {
    return `Widget ${descriptor.id?.slice(0, 8) ?? "Preview"}`;
  }

  if (descriptor.type === "lab-note") {
    return humanizeSlug(descriptor.slug ?? "Lab Note");
  }

  if (descriptor.type === "evolution") {
    return humanizeSlug(descriptor.slug ?? "Evolution");
  }

  if (descriptor.type === "archetype") {
    return humanizeSlug(descriptor.id ?? "Archetype");
  }

  return "Global Meta Snapshot";
}

function getBadge(descriptor: OgImageDescriptor): string {
  if (descriptor.type === "meta") {
    return new Date().toISOString().slice(0, 10);
  }

  if (descriptor.type === "widget" && descriptor.id) {
    return `w_${descriptor.id.slice(0, 12)}`;
  }

  return "trainerlab.io";
}

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ slug: string[] }> }
) {
  const resolved = await params;
  const descriptor = parseOgPath(resolved.slug);

  if (!descriptor) {
    return new Response("OG image not found", { status: 404 });
  }

  const title = getTitle(descriptor);
  const subtitle = getSubtitle(descriptor);
  const badge = getBadge(descriptor);

  return new ImageResponse(
    <div
      style={{
        height: "100%",
        width: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        background:
          "linear-gradient(140deg, rgb(15, 23, 42) 0%, rgb(17, 94, 89) 45%, rgb(30, 41, 59) 100%)",
        color: "rgb(248, 250, 252)",
        padding: "56px",
        fontFamily: "ui-sans-serif, system-ui, sans-serif",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "14px",
          }}
        >
          <div
            style={{
              width: "22px",
              height: "22px",
              borderRadius: "999px",
              background: "rgb(20, 184, 166)",
            }}
          />
          <div style={{ fontSize: "30px", fontWeight: 700 }}>TrainerLab</div>
        </div>
        <div
          style={{
            fontSize: "20px",
            padding: "8px 14px",
            borderRadius: "999px",
            background: "rgba(15, 23, 42, 0.5)",
            border: "1px solid rgba(148, 163, 184, 0.35)",
          }}
        >
          {badge}
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <div
          style={{
            fontSize: "26px",
            color: "rgb(167, 243, 208)",
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            fontWeight: 600,
          }}
        >
          {subtitle}
        </div>
        <div
          style={{
            fontSize: "70px",
            lineHeight: 1.05,
            fontWeight: 800,
            maxWidth: "1020px",
          }}
        >
          {title}
        </div>
      </div>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: "22px",
          color: "rgb(226, 232, 240)",
        }}
      >
        <div>Competitive intelligence for Pokemon TCG</div>
        <div style={{ fontWeight: 600 }}>trainerlab.io</div>
      </div>
    </div>,
    OG_SIZE
  );
}
