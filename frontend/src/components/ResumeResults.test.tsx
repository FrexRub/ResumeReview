import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  downloadResume,
  getActiveVacancyResumes,
  markResumeViewed,
} from "../api/client";
import type { VacancyResume } from "../types";
import { ResumeResults } from "./ResumeResults";

vi.mock("../api/client", () => {
  class ApiError extends Error {
    status = 500;
  }
  return {
    ApiError,
    downloadResume: vi.fn(),
    getActiveVacancyResumes: vi.fn(),
    markResumeViewed: vi.fn(),
  };
});

const mockedGetResumes = vi.mocked(getActiveVacancyResumes);
const mockedDownloadResume = vi.mocked(downloadResume);
const mockedMarkResumeViewed = vi.mocked(markResumeViewed);

const resumes: VacancyResume[] = [
  {
    id: "resume-1",
    title_vacancy: "python.txt",
    desired_position: "Python-разработчик",
    summary_resume: "Пять лет коммерческой разработки",
    score_label: "Высокое соответствие",
    candidate_rating: 91,
    recommendation: "Пригласить",
    recommendation_reason: "Релевантный опыт",
    executive_summary: "Сильный кандидат",
    short_conclusion: "Подходит",
    url_resume: "disk:/test/resume-1.docx",
    viewed: false,
  },
  {
    id: "resume-2",
    title_vacancy: "python.txt",
    desired_position: "Backend-разработчик",
    summary_resume: "Три года разработки API",
    score_label: "Среднее соответствие",
    candidate_rating: 76,
    recommendation: "Рассмотреть",
    recommendation_reason: "Требуется уточнить опыт",
    executive_summary: "Перспективный кандидат",
    short_conclusion: "Нужен звонок",
    url_resume: null,
    viewed: false,
  },
];

beforeEach(() => {
  mockedGetResumes.mockReset();
  mockedDownloadResume.mockReset();
  mockedDownloadResume.mockResolvedValue();
  mockedMarkResumeViewed.mockReset();
  mockedMarkResumeViewed.mockResolvedValue();
});

describe("ResumeResults", () => {
  it("renders fields, downloads the current resume and switches rows", async () => {
    mockedGetResumes.mockResolvedValue(resumes);
    const user = userEvent.setup();

    render(<ResumeResults />);

    expect(await screen.findByText("Python-разработчик")).toBeInTheDocument();
    expect(screen.getByText("91")).toBeInTheDocument();
    expect(screen.getByText("01 / 02")).toBeInTheDocument();
    expect(screen.queryByText("Ссылка на резюме")).not.toBeInTheDocument();
    expect(screen.queryByText("disk:/test/resume-1.docx")).not.toBeInTheDocument();
    expect(screen.queryByText("Просмотрено")).not.toBeInTheDocument();
    expect(screen.queryByText("ID записи")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Получение резюме" }));
    expect(mockedDownloadResume).toHaveBeenCalledWith("resume-1");

    await user.click(screen.getByRole("button", { name: "Следующее резюме" }));

    expect(screen.getByText("Backend-разработчик")).toBeInTheDocument();
    expect(screen.getByText("76")).toBeInTheDocument();
    expect(screen.getByText("02 / 02")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Получение резюме" })).toBeDisabled();
  });

  it("shows an empty state", async () => {
    mockedGetResumes.mockResolvedValue([]);

    render(<ResumeResults />);

    expect(
      await screen.findByText("Для активной вакансии пока нет непросмотренных резюме."),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Резюме изучено" }),
    ).not.toBeInTheDocument();
  });

  it("marks the current resume as viewed and shows the next one", async () => {
    mockedGetResumes.mockResolvedValue(resumes);

    render(<ResumeResults />);

    await userEvent.click(
      await screen.findByRole("button", { name: "Резюме изучено" }),
    );

    expect(mockedMarkResumeViewed).toHaveBeenCalledWith("resume-1");
    expect(screen.getByText("Backend-разработчик")).toBeInTheDocument();
    expect(screen.getByText("01 / 01")).toBeInTheDocument();
    expect(screen.queryByText("Python-разработчик")).not.toBeInTheDocument();
  });

  it("keeps the current resume visible when status update fails", async () => {
    mockedGetResumes.mockResolvedValue(resumes);
    mockedMarkResumeViewed.mockRejectedValue(new Error("database unavailable"));

    render(<ResumeResults />);

    await userEvent.click(
      await screen.findByRole("button", { name: "Резюме изучено" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Не удалось отметить резюме изученным",
    );
    expect(screen.getByText("Python-разработчик")).toBeInTheDocument();
  });
});
