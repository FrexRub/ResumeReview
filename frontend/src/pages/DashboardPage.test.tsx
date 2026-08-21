import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { AuthContext } from "../auth/AuthContext";
import { DashboardPage } from "./DashboardPage";

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return {
    ...actual,
    getActiveVacancy: vi.fn().mockResolvedValue(null),
    getActiveVacancyResumes: vi.fn().mockResolvedValue([]),
  };
});

const auth = {
  user: {
    id: "user-1",
    username: "admin",
    is_active: true,
    is_superuser: false,
    registered_at: "2026-08-18T10:00:00Z",
  },
  initializing: false,
  login: vi.fn(),
  logout: vi.fn(),
  changePassword: vi.fn(),
};

describe("DashboardPage", () => {
  it("places password management beside the current user", async () => {
    render(
      <MemoryRouter>
        <AuthContext.Provider value={auth}>
          <DashboardPage />
        </AuthContext.Provider>
      </MemoryRouter>,
    );

    const header = screen.getByRole("banner");
    const passwordButton = within(header).getByRole("button", {
      name: "Сменить пароль",
    });

    expect(passwordButton).toHaveAttribute("aria-expanded", "false");
    expect(
      within(screen.getByRole("complementary")).queryByRole("button", {
        name: "Сменить пароль",
      }),
    ).not.toBeInTheDocument();

    await userEvent.click(passwordButton);

    expect(passwordButton).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("heading", { name: "Смена пароля" })).toBeInTheDocument();
    expect(screen.getByLabelText("Текущий пароль")).toBeInTheDocument();
  });
});
