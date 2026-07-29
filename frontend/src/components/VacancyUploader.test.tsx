import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { parseVacancy, saveVacancy } from "../api/client";
import { VacancyUploader } from "./VacancyUploader";

vi.mock("../api/client", async () => {
  class ApiError extends Error {}
  return { ApiError, parseVacancy: vi.fn(), saveVacancy: vi.fn() };
});

const mockedParse = vi.mocked(parseVacancy);
const mockedSave = vi.mocked(saveVacancy);

beforeEach(() => {
  mockedParse.mockReset();
  mockedSave.mockReset();
});

describe("VacancyUploader", () => {
  it("rejects unsupported files", async () => {
    render(<VacancyUploader />);
    const input = screen.getByLabelText("Выбрать файл вакансии");
    fireEvent.change(input, { target: { files: [new File(["binary"], "vacancy.exe")] } });
    expect(screen.getByRole("alert")).toHaveTextContent("Этот формат пока не поддерживается");
  });

  it("uploads and renders parsed text", async () => {
    mockedParse.mockResolvedValue({
      status: "ok", filename: "vacancy.txt", mime_type: "text/plain", source_type: "text",
      characters: 16, text: "Python developer", warnings: [],
    });
    render(<VacancyUploader />);
    await userEvent.upload(
      screen.getByLabelText("Выбрать файл вакансии"),
      new File(["Python developer"], "vacancy.txt", { type: "text/plain" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Разобрать документ" }));
    expect(await screen.findByText("Python developer")).toBeInTheDocument();
    expect(mockedParse).toHaveBeenCalledOnce();
  });

  it("saves parsed text for candidate matching", async () => {
    mockedParse.mockResolvedValue({
      status: "ok", filename: "vacancy.txt", mime_type: "text/plain", source_type: "text",
      characters: 16, text: "Python developer", warnings: [],
    });
    mockedSave.mockResolvedValue({
      id: 1,
      created_at: "2026-07-29T20:00:00+03:00",
      is_active: true,
    });
    render(<VacancyUploader />);
    await userEvent.upload(
      screen.getByLabelText("Выбрать файл вакансии"),
      new File(["Python developer"], "vacancy.txt", { type: "text/plain" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Разобрать документ" }));
    await screen.findByText("Python developer");

    await userEvent.click(
      screen.getByRole("button", { name: "Добавить в подбор кандидатов" }),
    );

    expect(mockedSave).toHaveBeenCalledWith("Python developer");
    expect(
      await screen.findByText("Текст вакансии сохранён и готов к подбору кандидатов."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Добавлено в подбор кандидатов" }),
    ).toBeDisabled();
  });

  it("shows an error and allows retry when saving fails", async () => {
    mockedParse.mockResolvedValue({
      status: "ok", filename: "vacancy.txt", mime_type: "text/plain", source_type: "text",
      characters: 16, text: "Python developer", warnings: [],
    });
    mockedSave.mockRejectedValue(new Error("database unavailable"));
    render(<VacancyUploader />);
    await userEvent.upload(
      screen.getByLabelText("Выбрать файл вакансии"),
      new File(["Python developer"], "vacancy.txt", { type: "text/plain" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Разобрать документ" }));
    await screen.findByText("Python developer");

    await userEvent.click(
      screen.getByRole("button", { name: "Добавить в подбор кандидатов" }),
    );

    expect(
      await screen.findByText("Не удалось добавить вакансию в подбор кандидатов"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Добавить в подбор кандидатов" }),
    ).toBeEnabled();
  });
});
