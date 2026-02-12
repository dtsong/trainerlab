import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { AdminSidebar } from "../AdminSidebar";

const mockPathname = vi.fn(() => "/admin");

vi.mock("next/navigation", () => ({
  usePathname: () => mockPathname(),
}));

vi.mock("next/link", () => ({
  __esModule: true,
  default: ({
    href,
    children,
    className,
  }: {
    href: string;
    children: React.ReactNode;
    className?: string;
  }) => (
    <a href={href} className={className}>
      {children}
    </a>
  ),
}));

describe("AdminSidebar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPathname.mockReturnValue("/admin");
  });

  it("renders the Admin heading", () => {
    render(<AdminSidebar />);

    expect(screen.getByText("Admin")).toBeInTheDocument();
  });

  it("renders all navigation items", () => {
    render(<AdminSidebar />);

    expect(screen.getByText("Overview")).toBeInTheDocument();
    expect(screen.getByText("Access")).toBeInTheDocument();
    expect(screen.getByText("Tournaments")).toBeInTheDocument();
    expect(screen.getByText("Meta")).toBeInTheDocument();
    expect(screen.getByText("Cards")).toBeInTheDocument();
    expect(screen.getByText("Lab Notes")).toBeInTheDocument();
    expect(screen.getByText("Data")).toBeInTheDocument();
  });

  it("renders navigation links with correct hrefs", () => {
    render(<AdminSidebar />);

    expect(screen.getByText("Overview").closest("a")).toHaveAttribute(
      "href",
      "/admin"
    );
    expect(screen.getByText("Access").closest("a")).toHaveAttribute(
      "href",
      "/admin/access"
    );
    expect(screen.getByText("Tournaments").closest("a")).toHaveAttribute(
      "href",
      "/admin/tournaments"
    );
    expect(screen.getByText("Meta").closest("a")).toHaveAttribute(
      "href",
      "/admin/meta"
    );
    expect(screen.getByText("Cards").closest("a")).toHaveAttribute(
      "href",
      "/admin/cards"
    );
    expect(screen.getByText("Lab Notes").closest("a")).toHaveAttribute(
      "href",
      "/admin/lab-notes"
    );
    expect(screen.getByText("Data").closest("a")).toHaveAttribute(
      "href",
      "/admin/data"
    );
  });

  it("marks Overview as active when pathname is /admin", () => {
    mockPathname.mockReturnValue("/admin");
    render(<AdminSidebar />);

    const overviewLink = screen.getByText("Overview").closest("a")!;
    expect(overviewLink.className).toContain("bg-zinc-800");
    expect(overviewLink.className).toContain("text-zinc-100");
  });

  it("marks Tournaments as active when pathname starts with /admin/tournaments", () => {
    mockPathname.mockReturnValue("/admin/tournaments");
    render(<AdminSidebar />);

    const tournamentsLink = screen.getByText("Tournaments").closest("a")!;
    expect(tournamentsLink.className).toContain("bg-zinc-800");
    expect(tournamentsLink.className).toContain("text-zinc-100");

    // Overview should not be active
    const overviewLink = screen.getByText("Overview").closest("a")!;
    expect(overviewLink.className).toContain("text-zinc-400");
  });

  it("marks Lab Notes as active on nested lab notes route", () => {
    mockPathname.mockReturnValue("/admin/lab-notes/new");
    render(<AdminSidebar />);

    const labNotesLink = screen.getByText("Lab Notes").closest("a")!;
    expect(labNotesLink.className).toContain("bg-zinc-800");
    expect(labNotesLink.className).toContain("text-zinc-100");
  });

  it("does not mark Overview as active on sub-routes", () => {
    mockPathname.mockReturnValue("/admin/meta");
    render(<AdminSidebar />);

    const overviewLink = screen.getByText("Overview").closest("a")!;
    expect(overviewLink.className).toContain("text-zinc-400");
    expect(overviewLink.className).not.toContain("text-zinc-100");
  });

  it("marks Meta as active when pathname is /admin/meta", () => {
    mockPathname.mockReturnValue("/admin/meta");
    render(<AdminSidebar />);

    const metaLink = screen.getByText("Meta").closest("a")!;
    expect(metaLink.className).toContain("bg-zinc-800");
    expect(metaLink.className).toContain("text-zinc-100");
  });

  it("renders as an aside element with nav inside", () => {
    render(<AdminSidebar />);

    expect(screen.getByRole("complementary")).toBeInTheDocument();
    expect(screen.getByRole("navigation")).toBeInTheDocument();
  });
});
