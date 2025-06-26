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
          win_count: 150,
          last_win_date: "2024-01-01T00:00:00Z",
          image_path: "/test-image-1.jpg",
        },
        {
          rank: 2,
          person_id: 2,
          name: "Test Person 2",
          win_count: 120,
          last_win_date: "2024-01-02T00:00:00Z",
          image_path: "/test-image-2.jpg",
        },
      ],
      total_count: 2,
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
        search_timestamp: "2024-01-01T00:00:00Z",
        results: [
          {
            rank: 1,
            person_id: 1,
            name: "Test Person 1",
            similarity: 0.95,
            distance: 0.05,
            image_path: "/test-image-1.jpg",
          },
        ],
      });
    },
  ),

  // Persons list API (Actress list)
  http.get("http://backend:10000/api/persons", ({ request }) => {
    const url = new URL(request.url);
    const search = url.searchParams.get("search");
    const offset = Number(url.searchParams.get("offset")) || 0;

    // Default mock data
    let mockPersons = [
      {
        person_id: 1,
        name: "AIKA",
        image_path: "http://pics.dmm.co.jp/mono/actjpgs/aika3.jpg",
        dmm_actress_id: 1008887,
      },
      {
        person_id: 2,
        name: "AIKA（三浦あいか）",
        image_path: "http://pics.dmm.co.jp/mono/actjpgs/miura_aika.jpg",
        dmm_actress_id: 1105,
      },
      {
        person_id: 3,
        name: "愛上みお",
        image_path: "http://pics.dmm.co.jp/mono/actjpgs/aiue_mio.jpg",
        dmm_actress_id: 1075314,
      },
    ];

    // Handle search
    if (search) {
      if (search === "AIKA") {
        mockPersons = [
          {
            person_id: 1,
            name: "AIKA",
            image_path: "http://pics.dmm.co.jp/mono/actjpgs/aika3.jpg",
            dmm_actress_id: 1008887,
          },
          {
            person_id: 2,
            name: "AIKA（三浦あいか）",
            image_path: "http://pics.dmm.co.jp/mono/actjpgs/miura_aika.jpg",
            dmm_actress_id: 1105,
          },
        ];
      } else if (search === "あいだ") {
        mockPersons = [
          {
            person_id: 5,
            name: "あいだ希空",
            image_path: "http://pics.dmm.co.jp/mono/actjpgs/aida_noa.jpg",
            dmm_actress_id: 1080439,
          },
        ];
      }
    }

    // Handle pagination - must check offset before search to avoid conflicts
    if (offset === 20 && !search) {
      mockPersons = [
        {
          person_id: 21,
          name: "テスト女優21",
          image_path: "http://example.com/test21.jpg",
          dmm_actress_id: 21,
        },
        {
          person_id: 22,
          name: "テスト女優22",
          image_path: "http://example.com/test22.jpg",
          dmm_actress_id: 22,
        },
      ];
    }

    return HttpResponse.json({
      persons: mockPersons,
      total_count: search === "AIKA" ? 2 : search === "あいだ" ? 1 : offset === 20 ? 13010 : 13010,
      has_more: offset === 20 ? true : mockPersons.length >= 3,
    });
  }),
];
