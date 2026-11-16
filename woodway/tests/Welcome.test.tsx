import { fireEvent, render, screen } from "@testing-library/react";
import { Welcome } from "@/ui/Welcome";
import { useAtlas } from "@/store";

describe("Welcome", () => {
  beforeEach(() => useAtlas.setState({ welcomeSeen: false, lang: "en" }));

  it("says what the page is and offers the results first, the slides second", () => {
    render(<Welcome />);
    const dialog = screen.getByRole("dialog", { name: "Can trees save the climate?" });
    expect(dialog).toHaveTextContent("Timo Diepers");
    expect(dialog).toHaveTextContent("FaIR");
    expect(screen.getByRole("button", { name: "Explore the results" })).toHaveFocus();
    expect(screen.getByRole("link", { name: "View the slides" })).toHaveAttribute("target", "_blank");
    expect(dialog).toHaveTextContent("The slides are in German only.");
  });

  it("is retired by exploring, by the slides or by Escape, and remembered", () => {
    render(<Welcome />);
    fireEvent.click(screen.getByRole("button", { name: "Explore the results" }));
    expect(useAtlas.getState().welcomeSeen).toBe(true);
    expect(localStorage.getItem("atlas-welcome")).toBe("seen");
    useAtlas.setState({ welcomeSeen: false });
    fireEvent.keyDown(window, { key: "Escape" });
    expect(useAtlas.getState().welcomeSeen).toBe(true);
  });

  it("switches to German", () => {
    render(<Welcome />);
    fireEvent.click(screen.getByRole("button", { name: "de" }));
    expect(screen.getByRole("dialog", { name: "Können Bäume das Klima retten?" })).toBeInTheDocument();
  });
});
