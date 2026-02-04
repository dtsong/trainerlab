import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PanelOverlay } from "../panel-overlay";

describe("PanelOverlay", () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    children: <div data-testid="overlay-content">Panel content</div>,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    document.body.style.overflow = "";
  });

  describe("conditional rendering", () => {
    it("should render children when isOpen is true", () => {
      render(<PanelOverlay {...defaultProps} />);
      expect(screen.getByTestId("overlay-content")).toBeInTheDocument();
      expect(screen.getByText("Panel content")).toBeInTheDocument();
    });

    it("should not render anything when isOpen is false", () => {
      render(<PanelOverlay {...defaultProps} isOpen={false} />);
      expect(screen.queryByTestId("overlay-content")).not.toBeInTheDocument();
    });

    it("should render backdrop when open", () => {
      render(<PanelOverlay {...defaultProps} />);
      const backdrop = document.querySelector("[aria-hidden='true']");
      expect(backdrop).toBeInTheDocument();
    });
  });

  describe("body scroll lock", () => {
    it("should set body overflow to hidden when opened", () => {
      render(<PanelOverlay {...defaultProps} isOpen={true} />);
      expect(document.body.style.overflow).toBe("hidden");
    });

    it("should reset body overflow when closed", () => {
      render(<PanelOverlay {...defaultProps} isOpen={false} />);
      expect(document.body.style.overflow).toBe("");
    });

    it("should reset body overflow on unmount", () => {
      const { unmount } = render(
        <PanelOverlay {...defaultProps} isOpen={true} />
      );
      expect(document.body.style.overflow).toBe("hidden");

      unmount();
      expect(document.body.style.overflow).toBe("");
    });

    it("should toggle body overflow when isOpen changes", () => {
      const { rerender } = render(
        <PanelOverlay {...defaultProps} isOpen={false} />
      );
      expect(document.body.style.overflow).toBe("");

      rerender(<PanelOverlay {...defaultProps} isOpen={true} />);
      expect(document.body.style.overflow).toBe("hidden");

      rerender(<PanelOverlay {...defaultProps} isOpen={false} />);
      expect(document.body.style.overflow).toBe("");
    });
  });

  describe("escape key handler", () => {
    it("should call onClose when Escape key is pressed while open", () => {
      const onClose = vi.fn();
      render(<PanelOverlay {...defaultProps} onClose={onClose} />);

      fireEvent.keyDown(document, { key: "Escape" });
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it("should not call onClose when Escape key is pressed while closed", () => {
      const onClose = vi.fn();
      render(
        <PanelOverlay {...defaultProps} isOpen={false} onClose={onClose} />
      );

      fireEvent.keyDown(document, { key: "Escape" });
      expect(onClose).not.toHaveBeenCalled();
    });

    it("should not call onClose for non-Escape keys", () => {
      const onClose = vi.fn();
      render(<PanelOverlay {...defaultProps} onClose={onClose} />);

      fireEvent.keyDown(document, { key: "Enter" });
      fireEvent.keyDown(document, { key: "Tab" });
      fireEvent.keyDown(document, { key: "a" });
      expect(onClose).not.toHaveBeenCalled();
    });

    it("should remove keydown listener on unmount", () => {
      const onClose = vi.fn();
      const removeEventListenerSpy = vi.spyOn(document, "removeEventListener");

      const { unmount } = render(
        <PanelOverlay {...defaultProps} onClose={onClose} />
      );
      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        "keydown",
        expect.any(Function)
      );

      removeEventListenerSpy.mockRestore();
    });
  });

  describe("backdrop click", () => {
    it("should call onClose when backdrop is clicked", () => {
      const onClose = vi.fn();
      render(<PanelOverlay {...defaultProps} onClose={onClose} />);

      const backdrop = document.querySelector(
        "[aria-hidden='true']"
      ) as HTMLElement;
      fireEvent.click(backdrop);
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it("should not call onClose when content is clicked", () => {
      const onClose = vi.fn();
      render(<PanelOverlay {...defaultProps} onClose={onClose} />);

      fireEvent.click(screen.getByTestId("overlay-content"));
      expect(onClose).not.toHaveBeenCalled();
    });
  });

  describe("className handling", () => {
    it("should apply custom className to content wrapper", () => {
      render(<PanelOverlay {...defaultProps} className="custom-panel-class" />);
      const contentWrapper = screen
        .getByTestId("overlay-content")
        .closest(".relative.z-10") as HTMLElement;
      expect(contentWrapper).toHaveClass("custom-panel-class");
    });

    it("should always have relative and z-10 classes on content wrapper", () => {
      render(<PanelOverlay {...defaultProps} />);
      const contentWrapper = screen
        .getByTestId("overlay-content")
        .closest(".relative.z-10") as HTMLElement;
      expect(contentWrapper).toHaveClass("relative", "z-10");
    });
  });

  describe("overlay structure", () => {
    it("should render with fixed positioning and z-50", () => {
      render(<PanelOverlay {...defaultProps} />);
      const overlay = document.querySelector(".fixed.inset-0.z-50");
      expect(overlay).toBeInTheDocument();
    });

    it("should render backdrop with blur effect", () => {
      render(<PanelOverlay {...defaultProps} />);
      const backdrop = document.querySelector(
        "[aria-hidden='true']"
      ) as HTMLElement;
      expect(backdrop).toHaveClass("backdrop-blur-sm");
    });

    it("should render backdrop with semi-transparent background", () => {
      render(<PanelOverlay {...defaultProps} />);
      const backdrop = document.querySelector(
        "[aria-hidden='true']"
      ) as HTMLElement;
      expect(backdrop).toHaveClass("bg-black/50");
    });

    it("should render backdrop with full opacity when open", () => {
      render(<PanelOverlay {...defaultProps} />);
      const backdrop = document.querySelector(
        "[aria-hidden='true']"
      ) as HTMLElement;
      expect(backdrop).toHaveClass("opacity-100");
    });
  });
});
