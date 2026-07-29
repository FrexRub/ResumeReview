import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import App from "./App";
import { AuthContext } from "./auth/AuthContext";

const guestAuth = {
  user: null,
  initializing: false,
  login: vi.fn(),
  logout: vi.fn(),
  changePassword: vi.fn(),
};

describe("protected routing", () => {
  it("redirects guests from dashboard", async () => {
    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <AuthContext.Provider value={guestAuth}>
          <App />
        </AuthContext.Provider>
      </MemoryRouter>,
    );
    expect(await screen.findByRole("heading", { name: "Продолжить работу" })).toBeInTheDocument();
  });
});
