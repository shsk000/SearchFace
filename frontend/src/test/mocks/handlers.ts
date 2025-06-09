import { http, HttpResponse } from "msw";

export const handlers = [
  // Search API
  http.post("http://backend:10000/api/search", () => {
    return HttpResponse.json({
      results: [
        {
          name: "Test Person 1",
          similarity: 0.95,
          distance: 0.05,
          image_path: "/test-image-1.jpg",
        },
        {
          name: "Test Person 2",
          similarity: 0.87,
          distance: 0.13,
          image_path: "/test-image-2.jpg",
        },
      ],
      processing_time: 0.123,
      search_session_id: "test-session-123",
    });
  }),

  // Ranking API
  http.get("http://backend:10000/api/ranking", () => {
    return HttpResponse.json({
      ranking: [
        {
          rank: 1,
          person_id: 1,
          name: "Test Person 1",
          search_count: 150,
          image_url: "/test-image-1.jpg",
        },
        {
          rank: 2,
          person_id: 2,
          name: "Test Person 2",
          search_count: 120,
          image_url: "/test-image-2.jpg",
        },
      ],
    });
  }),

  // Person detail API
  http.get(
    "http://backend:10000/api/persons/:personId",
    ({ params }: { params: Record<string, string> }) => {
      const { personId } = params;
      return HttpResponse.json({
        person_id: Number(personId),
        name: `Test Actress ${personId}`,
        image_path: `/test-actress-${personId}.jpg`,
        search_count: 10,
      });
    },
  ),

  // Session results API
  http.get(
    "http://backend:10000/api/search/:sessionId",
    ({ params }: { params: Record<string, string> }) => {
      const { sessionId } = params;
      return HttpResponse.json({
        session_id: sessionId,
        results: [
          {
            id: 1,
            name: "Test Person 1",
            similarity: 0.95,
            image_url: "/test-image-1.jpg",
          },
        ],
        created_at: "2024-01-01T00:00:00Z",
      });
    },
  ),
];
