import "@testing-library/jest-dom";
import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll } from "vitest";
import { server } from "./src/test/mocks/server";

// Start server before all tests
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));

// Clean up after each test case (React Testing Library)
afterEach(() => {
  cleanup();
  server.resetHandlers();
});

// Clean up after all tests
afterAll(() => server.close());
