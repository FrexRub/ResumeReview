import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { deactivateActiveVacancy, getActiveVacancy } from "../api/client";
import { CurrentVacancy } from "./CurrentVacancy";

vi.mock("../api/client", async () => {
  class ApiError extends Error {}
  return {
    ApiError,
    deactivateActiveVacancy: vi.fn(),
    getActiveVacancy: vi.fn(),
  };
});

const mockedGetActiveVacancy = vi.mocked(getActiveVacancy);
const mockedDeactivateActiveVacancy = vi.mocked(deactivateActiveVacancy);

beforeEach(() => {
  mockedGetActiveVacancy.mockReset();
  mockedDeactivateActiveVacancy.mockReset();
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

  it("deactivates the current vacancy by clicking its status", async () => {
    mockedGetActiveVacancy.mockResolvedValue({
      id: 7,
      created_at: "2026-08-20T10:00:00Z",
      filename: "backend-developer.txt",
      content: "Backend Developer",
      is_active: true,
    });
    mockedDeactivateActiveVacancy.mockResolvedValue({
      id: 7,
      created_at: "2026-08-20T10:00:00Z",
      is_active: false,
    });

    render(<CurrentVacancy />);

    await userEvent.click(
      await screen.findByRole("button", {
        name: "Деактивировать текущую вакансию",
      }),
    );

    expect(mockedDeactivateActiveVacancy).toHaveBeenCalledOnce();
    expect(
      await screen.findByText(/Активная вакансия пока не выбрана/),
    ).toBeInTheDocument();
  });

  it("keeps the vacancy visible when deactivation fails", async () => {
    mockedGetActiveVacancy.mockResolvedValue({
      id: 7,
      created_at: "2026-08-20T10:00:00Z",
      filename: "backend-developer.txt",
      content: "Backend Developer",
      is_active: true,
    });
    mockedDeactivateActiveVacancy.mockRejectedValue(new Error("database unavailable"));

    render(<CurrentVacancy />);

    await userEvent.click(
      await screen.findByRole("button", {
        name: "Деактивировать текущую вакансию",
      }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Не удалось деактивировать вакансию",
    );
    expect(screen.getByText("backend-developer.txt")).toBeInTheDocument();
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
