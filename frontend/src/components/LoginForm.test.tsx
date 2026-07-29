import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { LoginForm } from "./LoginForm";

describe("LoginForm", () => {
  it("validates empty fields", async () => {
    const submit = vi.fn();
    render(<LoginForm onSubmit={submit} />);
    await userEvent.click(screen.getByRole("button", { name: "Войти в кабинет" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Введите имя пользователя и пароль");
    expect(submit).not.toHaveBeenCalled();
  });

  it("submits credentials", async () => {
    const submit = vi.fn().mockResolvedValue(undefined);
    render(<LoginForm onSubmit={submit} />);
    await userEvent.type(screen.getByLabelText("Имя пользователя"), "revisor");
    await userEvent.type(screen.getByLabelText("Пароль"), "Strong!Pass1");
    await userEvent.click(screen.getByRole("button", { name: "Войти в кабинет" }));
    expect(submit).toHaveBeenCalledWith("revisor", "Strong!Pass1");
  });
});
