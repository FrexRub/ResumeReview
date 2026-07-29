import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { parseVacancy } from "../api/client";
import { VacancyUploader } from "./VacancyUploader";

vi.mock("../api/client", async () => {
  class ApiError extends Error {}
  return { ApiError, parseVacancy: vi.fn() };
});

const mockedParse = vi.mocked(parseVacancy);

beforeEach(() => mockedParse.mockReset());

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
});
