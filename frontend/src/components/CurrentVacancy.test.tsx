import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getActiveVacancy } from "../api/client";
import { CurrentVacancy } from "./CurrentVacancy";

vi.mock("../api/client", async () => {
  class ApiError extends Error {}
  return { ApiError, getActiveVacancy: vi.fn() };
});

const mockedGetActiveVacancy = vi.mocked(getActiveVacancy);

beforeEach(() => {
  mockedGetActiveVacancy.mockReset();
});

describe("CurrentVacancy", () => {
  it("renders content of the current active vacancy", async () => {
    mockedGetActiveVacancy.mockResolvedValue({
      id: 7,
      created_at: "2026-08-20T10:00:00Z",
      filename: "backend-developer.txt",
      content: "Backend Developer\nPython, FastAPI, PostgreSQL",
      is_active: true,
    });

    render(<CurrentVacancy />);

    expect(await screen.findByText("backend-developer.txt")).toBeInTheDocument();
    expect(screen.getByLabelText("Текст текущей вакансии")).toHaveTextContent(
      "Backend Developer Python, FastAPI, PostgreSQL",
    );
    expect(screen.getByText("Активна")).toBeInTheDocument();
  });

  it("shows the empty state when there is no active vacancy", async () => {
    mockedGetActiveVacancy.mockResolvedValue(null);

    render(<CurrentVacancy />);

    expect(
      await screen.findByText(/Активная вакансия пока не выбрана/),
    ).toBeInTheDocument();
  });

  it("allows retry after a loading error", async () => {
    mockedGetActiveVacancy
      .mockRejectedValueOnce(new Error("database unavailable"))
      .mockResolvedValueOnce(null);

    render(<CurrentVacancy />);

    await userEvent.click(await screen.findByRole("button", { name: "Повторить" }));

    expect(mockedGetActiveVacancy).toHaveBeenCalledTimes(2);
    expect(
      await screen.findByText(/Активная вакансия пока не выбрана/),
    ).toBeInTheDocument();
  });
});
