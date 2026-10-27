export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export const OFFLINE_MESSAGE = "Нет связи с программой. Проверьте, что Vymova запущена, и обновите страницу.";

/** FastAPI sends `detail` as a Russian string for our own errors and as a list for schema errors. */
export function detailMessage(body: unknown, status: number): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string" && detail.trim()) return detail;
    if (Array.isArray(detail)) return "Проверьте введённые данные.";
  }
  if (status >= 500) return "Программа ответила ошибкой. Попробуйте ещё раз через минуту.";
  return `Не получилось (код ${status}).`;
}
