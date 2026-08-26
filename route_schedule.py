"""회사 제공 엑셀 시간표에서 빌드 시 생성된 정적 노선 데이터.

이 파일은 앱 실행 중 엑셀 파일을 읽지 않는다. 원본 변경 시
``tools_generate_route_schedule.py``를 다시 실행해 갱신한다.
"""

from __future__ import annotations

from typing import Any, Mapping


SERVICE_WEEKDAY = "weekday"
SERVICE_SATURDAY = "saturday"
SERVICE_SUNDAY_HOLIDAY = "sunday_holiday"
SERVICE_LABELS = {
    SERVICE_WEEKDAY: "평일",
    SERVICE_SATURDAY: "토요일",
    SERVICE_SUNDAY_HOLIDAY: "일요일(공휴일)",
}
DEPOT_ROUTES = {
    "미추홀": ("76", "77", "75", "12"),
    "제물포": ("30", "78", "급행97"),
}
STATUS_TO_SHIFT = {"오전": "morning", "오후": "afternoon"}

ROUTE_SCHEDULES = {
    "76": {
        "weekday": {
            "label": "평일",
            "fleet_count": 7,
            "orders": {
                "1": {
                    "morning": {
                        "time": "04:55",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:15",
                        "departure": ""
                    }
                },
                "2": {
                    "morning": {
                        "time": "05:25",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:45",
                        "departure": ""
                    }
                },
                "3": {
                    "morning": {
                        "time": "05:50",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:15",
                        "departure": ""
                    }
                },
                "4": {
                    "morning": {
                        "time": "06:15",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:40",
                        "departure": ""
                    }
                },
                "5": {
                    "morning": {
                        "time": "06:35",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:05",
                        "departure": ""
                    }
                },
                "6": {
                    "morning": {
                        "time": "06:55",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:30",
                        "departure": ""
                    }
                },
                "7": {
                    "morning": {
                        "time": "07:20",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "13:45",
                        "departure": ""
                    }
                }
            }
        },
        "saturday": {
            "label": "토요일",
            "fleet_count": 6,
            "orders": {
                "1": {
                    "morning": {
                        "time": "04:55",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:15",
                        "departure": ""
                    }
                },
                "2": {
                    "morning": {
                        "time": "05:30",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:50",
                        "departure": ""
                    }
                },
                "3": {
                    "morning": {
                        "time": "06:00",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:25",
                        "departure": ""
                    }
                },
                "4": {
                    "morning": {
                        "time": "06:30",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:00",
                        "departure": ""
                    }
                },
                "5": {
                    "morning": {
                        "time": "06:55",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:30",
                        "departure": ""
                    }
                },
                "6": {
                    "morning": {
                        "time": "07:20",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "13:40",
                        "departure": ""
                    }
                }
            }
        },
        "sunday_holiday": {
            "label": "일요일(공휴일)",
            "fleet_count": 5,
            "orders": {
                "1": {
                    "morning": {
                        "time": "04:55",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:20",
                        "departure": ""
                    }
                },
                "2": {
                    "morning": {
                        "time": "05:30",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:00",
                        "departure": ""
                    }
                },
                "3": {
                    "morning": {
                        "time": "06:05",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:40",
                        "departure": ""
                    }
                },
                "4": {
                    "morning": {
                        "time": "06:40",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:20",
                        "departure": ""
                    }
                },
                "5": {
                    "morning": {
                        "time": "07:15",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "13:40",
                        "departure": ""
                    }
                }
            }
        }
    },
    "77": {
        "weekday": {
            "label": "평일",
            "fleet_count": 6,
            "orders": {
                "1": {
                    "morning": {
                        "time": "04:50",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:10",
                        "departure": ""
                    }
                },
                "2": {
                    "morning": {
                        "time": "05:30",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:40",
                        "departure": ""
                    }
                },
                "3": {
                    "morning": {
                        "time": "06:00",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:10",
                        "departure": ""
                    }
                },
                "4": {
                    "morning": {
                        "time": "06:25",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:40",
                        "departure": ""
                    }
                },
                "5": {
                    "morning": {
                        "time": "05:15",
                        "departure": "계양역"
                    },
                    "afternoon": {
                        "time": "13:10",
                        "departure": ""
                    }
                },
                "6": {
                    "morning": {
                        "time": "05:35",
                        "departure": "계양역"
                    },
                    "afternoon": {
                        "time": "13:40",
                        "departure": ""
                    }
                }
            }
        },
        "saturday": {
            "label": "토요일",
            "fleet_count": 5,
            "orders": {
                "1": {
                    "morning": {
                        "time": "04:50",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:30",
                        "departure": ""
                    }
                },
                "2": {
                    "morning": {
                        "time": "05:30",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:10",
                        "departure": ""
                    }
                },
                "3": {
                    "morning": {
                        "time": "06:10",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:50",
                        "departure": ""
                    }
                },
                "4": {
                    "morning": {
                        "time": "05:15",
                        "departure": "계양역"
                    },
                    "afternoon": {
                        "time": "13:10",
                        "departure": ""
                    }
                },
                "5": {
                    "morning": {
                        "time": "05:40",
                        "departure": "계양역"
                    },
                    "afternoon": {
                        "time": "13:50",
                        "departure": ""
                    }
                }
            }
        },
        "sunday_holiday": {
            "label": "일요일(공휴일)",
            "fleet_count": 5,
            "orders": {
                "1": {
                    "morning": {
                        "time": "04:50",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:30",
                        "departure": ""
                    }
                },
                "2": {
                    "morning": {
                        "time": "05:30",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:10",
                        "departure": ""
                    }
                },
                "3": {
                    "morning": {
                        "time": "06:10",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:50",
                        "departure": ""
                    }
                },
                "4": {
                    "morning": {
                        "time": "05:15",
                        "departure": "계양역"
                    },
                    "afternoon": {
                        "time": "13:10",
                        "departure": ""
                    }
                },
                "5": {
                    "morning": {
                        "time": "05:40",
                        "departure": "계양역"
                    },
                    "afternoon": {
                        "time": "13:50",
                        "departure": ""
                    }
                }
            }
        }
    },
    "75": {
        "weekday": {
            "label": "평일",
            "fleet_count": 10,
            "orders": {
                "1": {
                    "morning": {
                        "time": "05:00",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:13",
                        "departure": ""
                    }
                },
                "2": {
                    "morning": {
                        "time": "05:15",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:29",
                        "departure": ""
                    }
                },
                "3": {
                    "morning": {
                        "time": "05:30",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "13:05",
                        "departure": ""
                    }
                },
                "4": {
                    "morning": {
                        "time": "05:45",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "13:21",
                        "departure": ""
                    }
                },
                "5": {
                    "morning": {
                        "time": "06:00",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "13:37",
                        "departure": ""
                    }
                },
                "6": {
                    "morning": {
                        "time": "06:13",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "13:53",
                        "departure": ""
                    }
                },
                "7": {
                    "morning": {
                        "time": "06:26",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:09",
                        "departure": ""
                    }
                },
                "8": {
                    "morning": {
                        "time": "06:39",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:25",
                        "departure": ""
                    }
                },
                "9": {
                    "morning": {
                        "time": "06:52",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:41",
                        "departure": ""
                    }
                },
                "10": {
                    "morning": {
                        "time": "07:05",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:57",
                        "departure": ""
                    }
                }
            }
        },
        "saturday": {
            "label": "토요일",
            "fleet_count": 8,
            "orders": {
                "1": {
                    "morning": {
                        "time": "05:00",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:20",
                        "departure": ""
                    }
                },
                "2": {
                    "morning": {
                        "time": "05:20",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "13:00",
                        "departure": ""
                    }
                },
                "3": {
                    "morning": {
                        "time": "05:40",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "13:20",
                        "departure": ""
                    }
                },
                "4": {
                    "morning": {
                        "time": "06:00",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "13:40",
                        "departure": ""
                    }
                },
                "5": {
                    "morning": {
                        "time": "06:19",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:00",
                        "departure": ""
                    }
                },
                "6": {
                    "morning": {
                        "time": "06:38",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:20",
                        "departure": ""
                    }
                },
                "7": {
                    "morning": {
                        "time": "06:57",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:40",
                        "departure": ""
                    }
                },
                "8": {
                    "morning": {
                        "time": "07:16",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:00",
                        "departure": ""
                    }
                }
            }
        },
        "sunday_holiday": {
            "label": "일요일(공휴일)",
            "fleet_count": 7,
            "orders": {
                "1": {
                    "morning": {
                        "time": "05:00",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:16",
                        "departure": ""
                    }
                },
                "2": {
                    "morning": {
                        "time": "05:22",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "13:04",
                        "departure": ""
                    }
                },
                "3": {
                    "morning": {
                        "time": "05:44",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "13:26",
                        "departure": ""
                    }
                },
                "4": {
                    "morning": {
                        "time": "06:06",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "13:48",
                        "departure": ""
                    }
                },
                "5": {
                    "morning": {
                        "time": "06:28",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:10",
                        "departure": ""
                    }
                },
                "6": {
                    "morning": {
                        "time": "06:50",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:32",
                        "departure": ""
                    }
                },
                "7": {
                    "morning": {
                        "time": "07:12",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:54",
                        "departure": ""
                    }
                }
            }
        }
    },
    "12": {
        "weekday": {
            "label": "평일",
            "fleet_count": 33,
            "orders": {
                "1": {
                    "morning": {
                        "time": "04:50",
                        "departure": "루원하"
                    },
                    "afternoon": {
                        "time": "12:00",
                        "departure": ""
                    }
                },
                "2": {
                    "morning": {
                        "time": "04:56",
                        "departure": "루원하"
                    },
                    "afternoon": {
                        "time": "12:10",
                        "departure": ""
                    }
                },
                "3": {
                    "morning": {
                        "time": "05:02",
                        "departure": "루원하"
                    },
                    "afternoon": {
                        "time": "12:20",
                        "departure": ""
                    }
                },
                "4": {
                    "morning": {
                        "time": "05:08",
                        "departure": "루원하"
                    },
                    "afternoon": {
                        "time": "12:30",
                        "departure": ""
                    }
                },
                "5": {
                    "morning": {
                        "time": "05:14",
                        "departure": "루원하"
                    },
                    "afternoon": {
                        "time": "12:40",
                        "departure": ""
                    }
                },
                "6": {
                    "morning": {
                        "time": "05:20",
                        "departure": "루원하"
                    },
                    "afternoon": {
                        "time": "12:50",
                        "departure": ""
                    }
                },
                "7": {
                    "morning": {
                        "time": "05:26",
                        "departure": "루원하"
                    },
                    "afternoon": {
                        "time": "13:00",
                        "departure": ""
                    }
                },
                "8": {
                    "morning": {
                        "time": "05:32",
                        "departure": "루원하"
                    },
                    "afternoon": {
                        "time": "13:10",
                        "departure": ""
                    }
                },
                "9": {
                    "morning": {
                        "time": "05:38",
                        "departure": "루원하"
                    },
                    "afternoon": {
                        "time": "13:20",
                        "departure": ""
                    }
                },
                "10": {
                    "morning": {
                        "time": "05:00",
                        "departure": "일신동"
                    },
                    "afternoon": {
                        "time": "13:30",
                        "departure": ""
                    }
                },
                "11": {
                    "morning": {
                        "time": "05:07",
                        "departure": "일신동"
                    },
                    "afternoon": {
                        "time": "13:40",
                        "departure": ""
                    }
                },
                "12": {
                    "morning": {
                        "time": "05:14",
                        "departure": "일신동"
                    },
                    "afternoon": {
                        "time": "13:50",
                        "departure": ""
                    }
                },
                "13": {
                    "morning": {
                        "time": "05:21",
                        "departure": "일신동"
                    },
                    "afternoon": {
                        "time": "14:00",
                        "departure": ""
                    }
                },
                "14": {
                    "morning": {
                        "time": "05:28",
                        "departure": "일신동"
                    },
                    "afternoon": {
                        "time": "14:09",
                        "departure": ""
                    }
                },
                "15": {
                    "morning": {
                        "time": "05:35",
                        "departure": "일신동"
                    },
                    "afternoon": {
                        "time": "14:18",
                        "departure": ""
                    }
                },
                "16": {
                    "morning": {
                        "time": "05:42",
                        "departure": "일신동"
                    },
                    "afternoon": {
                        "time": "14:27",
                        "departure": ""
                    }
                },
                "17": {
                    "morning": {
                        "time": "05:49",
                        "departure": "일신동"
                    },
                    "afternoon": {
                        "time": "14:36",
                        "departure": ""
                    }
                },
                "18": {
                    "morning": {
                        "time": "05:56",
                        "departure": "일신동"
                    },
                    "afternoon": {
                        "time": "14:45",
                        "departure": ""
                    }
                },
                "19": {
                    "morning": {
                        "time": "05:00",
                        "departure": "루원상"
                    },
                    "afternoon": {
                        "time": "14:54",
                        "departure": ""
                    }
                },
                "20": {
                    "morning": {
                        "time": "05:00",
                        "departure": "가좌농협"
                    },
                    "afternoon": {
                        "time": "15:03",
                        "departure": ""
                    }
                },
                "21": {
                    "morning": {
                        "time": "05:08",
                        "departure": "가좌농협"
                    },
                    "afternoon": {
                        "time": "15:12",
                        "departure": ""
                    }
                },
                "22": {
                    "morning": {
                        "time": "05:16",
                        "departure": "가좌농협"
                    },
                    "afternoon": {
                        "time": "15:21",
                        "departure": ""
                    }
                },
                "23": {
                    "morning": {
                        "time": "04:40",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "15:30",
                        "departure": ""
                    }
                },
                "24": {
                    "morning": {
                        "time": "04:50",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "15:39",
                        "departure": ""
                    }
                },
                "25": {
                    "morning": {
                        "time": "05:00",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "15:48",
                        "departure": ""
                    }
                },
                "26": {
                    "morning": {
                        "time": "05:10",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "15:57",
                        "departure": ""
                    }
                },
                "27": {
                    "morning": {
                        "time": "05:20",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "16:06",
                        "departure": ""
                    }
                },
                "28": {
                    "morning": {
                        "time": "05:30",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "16:15",
                        "departure": ""
                    }
                },
                "29": {
                    "morning": {
                        "time": "05:40",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "16:24",
                        "departure": ""
                    }
                },
                "30": {
                    "morning": {
                        "time": "05:50",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "16:33",
                        "departure": ""
                    }
                },
                "31": {
                    "morning": {
                        "time": "06:00",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "16:42",
                        "departure": ""
                    }
                },
                "32": {
                    "morning": {
                        "time": "06:10",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "16:51",
                        "departure": ""
                    }
                },
                "33": {
                    "morning": {
                        "time": "06:20",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "17:00",
                        "departure": ""
                    }
                }
            }
        },
        "saturday": {
            "label": "토요일",
            "fleet_count": 25,
            "orders": {
                "1": {
                    "morning": {
                        "time": "04:50",
                        "departure": "루원하"
                    },
                    "afternoon": {
                        "time": "12:13",
                        "departure": ""
                    }
                },
                "2": {
                    "morning": {
                        "time": "04:59",
                        "departure": "루원하"
                    },
                    "afternoon": {
                        "time": "12:24",
                        "departure": ""
                    }
                },
                "3": {
                    "morning": {
                        "time": "05:08",
                        "departure": "루원하"
                    },
                    "afternoon": {
                        "time": "12:35",
                        "departure": ""
                    }
                },
                "4": {
                    "morning": {
                        "time": "05:17",
                        "departure": "루원하"
                    },
                    "afternoon": {
                        "time": "12:46",
                        "departure": ""
                    }
                },
                "5": {
                    "morning": {
                        "time": "05:26",
                        "departure": "루원하"
                    },
                    "afternoon": {
                        "time": "12:57",
                        "departure": ""
                    }
                },
                "6": {
                    "morning": {
                        "time": "05:35",
                        "departure": "루원하"
                    },
                    "afternoon": {
                        "time": "13:09",
                        "departure": ""
                    }
                },
                "7": {
                    "morning": {
                        "time": "05:00",
                        "departure": "일신동"
                    },
                    "afternoon": {
                        "time": "13:21",
                        "departure": ""
                    }
                },
                "8": {
                    "morning": {
                        "time": "05:10",
                        "departure": "일신동"
                    },
                    "afternoon": {
                        "time": "13:33",
                        "departure": ""
                    }
                },
                "9": {
                    "morning": {
                        "time": "05:20",
                        "departure": "일신동"
                    },
                    "afternoon": {
                        "time": "13:45",
                        "departure": ""
                    }
                },
                "10": {
                    "morning": {
                        "time": "05:30",
                        "departure": "일신동"
                    },
                    "afternoon": {
                        "time": "13:57",
                        "departure": ""
                    }
                },
                "11": {
                    "morning": {
                        "time": "05:40",
                        "departure": "일신동"
                    },
                    "afternoon": {
                        "time": "14:10",
                        "departure": ""
                    }
                },
                "12": {
                    "morning": {
                        "time": "05:50",
                        "departure": "일신동"
                    },
                    "afternoon": {
                        "time": "14:23",
                        "departure": ""
                    }
                },
                "13": {
                    "morning": {
                        "time": "05:00",
                        "departure": "루원상"
                    },
                    "afternoon": {
                        "time": "14:36",
                        "departure": ""
                    }
                },
                "14": {
                    "morning": {
                        "time": "05:00",
                        "departure": "가좌농협"
                    },
                    "afternoon": {
                        "time": "14:49",
                        "departure": ""
                    }
                },
                "15": {
                    "morning": {
                        "time": "05:15",
                        "departure": "가좌농협"
                    },
                    "afternoon": {
                        "time": "15:02",
                        "departure": ""
                    }
                },
                "16": {
                    "morning": {
                        "time": "04:40",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "15:15",
                        "departure": ""
                    }
                },
                "17": {
                    "morning": {
                        "time": "04:52",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "15:28",
                        "departure": ""
                    }
                },
                "18": {
                    "morning": {
                        "time": "05:04",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "15:41",
                        "departure": ""
                    }
                },
                "19": {
                    "morning": {
                        "time": "05:16",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "15:54",
                        "departure": ""
                    }
                },
                "20": {
                    "morning": {
                        "time": "05:28",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "16:07",
                        "departure": ""
                    }
                },
                "21": {
                    "morning": {
                        "time": "05:40",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "16:20",
                        "departure": ""
                    }
                },
                "22": {
                    "morning": {
                        "time": "05:52",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "16:33",
                        "departure": ""
                    }
                },
                "23": {
                    "morning": {
                        "time": "06:04",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "16:46",
                        "departure": ""
                    }
                },
                "24": {
                    "morning": {
                        "time": "06:16",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "16:59",
                        "departure": ""
                    }
                },
                "25": {
                    "morning": {
                        "time": "06:28",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "17:12",
                        "departure": ""
                    }
                }
            }
        },
        "sunday_holiday": {
            "label": "일요일(공휴일)",
            "fleet_count": 22,
            "orders": {
                "1": {
                    "morning": {
                        "time": "04:50",
                        "departure": "루원하"
                    },
                    "afternoon": {
                        "time": "12:13",
                        "departure": ""
                    }
                },
                "2": {
                    "morning": {
                        "time": "05:01",
                        "departure": "루원하"
                    },
                    "afternoon": {
                        "time": "12:24",
                        "departure": ""
                    }
                },
                "3": {
                    "morning": {
                        "time": "05:12",
                        "departure": "루원하"
                    },
                    "afternoon": {
                        "time": "12:35",
                        "departure": ""
                    }
                },
                "4": {
                    "morning": {
                        "time": "05:23",
                        "departure": "루원하"
                    },
                    "afternoon": {
                        "time": "12:46",
                        "departure": ""
                    }
                },
                "5": {
                    "morning": {
                        "time": "05:34",
                        "departure": "루원하"
                    },
                    "afternoon": {
                        "time": "12:57",
                        "departure": ""
                    }
                },
                "6": {
                    "morning": {
                        "time": "05:00",
                        "departure": "일신동"
                    },
                    "afternoon": {
                        "time": "13:21",
                        "departure": ""
                    }
                },
                "7": {
                    "morning": {
                        "time": "05:12",
                        "departure": "일신동"
                    },
                    "afternoon": {
                        "time": "13:33",
                        "departure": ""
                    }
                },
                "8": {
                    "morning": {
                        "time": "05:24",
                        "departure": "일신동"
                    },
                    "afternoon": {
                        "time": "13:45",
                        "departure": ""
                    }
                },
                "9": {
                    "morning": {
                        "time": "05:36",
                        "departure": "일신동"
                    },
                    "afternoon": {
                        "time": "13:57",
                        "departure": ""
                    }
                },
                "10": {
                    "morning": {
                        "time": "05:48",
                        "departure": "일신동"
                    },
                    "afternoon": {
                        "time": "14:10",
                        "departure": ""
                    }
                },
                "11": {
                    "morning": {
                        "time": "05:00",
                        "departure": "루원상"
                    },
                    "afternoon": {
                        "time": "14:36",
                        "departure": ""
                    }
                },
                "12": {
                    "morning": {
                        "time": "05:00",
                        "departure": "가좌농협"
                    },
                    "afternoon": {
                        "time": "14:49",
                        "departure": ""
                    }
                },
                "13": {
                    "morning": {
                        "time": "05:15",
                        "departure": "가좌농협"
                    },
                    "afternoon": {
                        "time": "15:02",
                        "departure": ""
                    }
                },
                "14": {
                    "morning": {
                        "time": "04:40",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "15:15",
                        "departure": ""
                    }
                },
                "15": {
                    "morning": {
                        "time": "04:54",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "15:28",
                        "departure": ""
                    }
                },
                "16": {
                    "morning": {
                        "time": "05:08",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "15:41",
                        "departure": ""
                    }
                },
                "17": {
                    "morning": {
                        "time": "05:22",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "15:54",
                        "departure": ""
                    }
                },
                "18": {
                    "morning": {
                        "time": "05:36",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "16:07",
                        "departure": ""
                    }
                },
                "19": {
                    "morning": {
                        "time": "05:50",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "16:20",
                        "departure": ""
                    }
                },
                "20": {
                    "morning": {
                        "time": "06:04",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "16:33",
                        "departure": ""
                    }
                },
                "21": {
                    "morning": {
                        "time": "06:18",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "16:46",
                        "departure": ""
                    }
                },
                "22": {
                    "morning": {
                        "time": "06:32",
                        "departure": "연안부두"
                    },
                    "afternoon": {
                        "time": "16:59",
                        "departure": ""
                    }
                }
            }
        }
    },
    "78": {
        "weekday": {
            "label": "평일",
            "fleet_count": 8,
            "orders": {
                "1": {
                    "morning": {
                        "time": "05:00",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "13:54",
                        "departure": ""
                    }
                },
                "2": {
                    "morning": {
                        "time": "05:18",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:21",
                        "departure": ""
                    }
                },
                "3": {
                    "morning": {
                        "time": "05:36",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:48",
                        "departure": ""
                    }
                },
                "4": {
                    "morning": {
                        "time": "05:54",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:15",
                        "departure": ""
                    }
                },
                "5": {
                    "morning": {
                        "time": "06:12",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:42",
                        "departure": ""
                    }
                },
                "6": {
                    "morning": {
                        "time": "06:30",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:09",
                        "departure": ""
                    }
                },
                "7": {
                    "morning": {
                        "time": "06:48",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:35",
                        "departure": ""
                    }
                },
                "8": {
                    "morning": {
                        "time": "07:06",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "13:27",
                        "departure": ""
                    }
                }
            }
        },
        "saturday": {
            "label": "토요일",
            "fleet_count": 6,
            "orders": {
                "1": {
                    "morning": {
                        "time": "05:00",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:40",
                        "departure": ""
                    }
                },
                "2": {
                    "morning": {
                        "time": "05:25",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:15",
                        "departure": ""
                    }
                },
                "3": {
                    "morning": {
                        "time": "05:50",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:50",
                        "departure": ""
                    }
                },
                "4": {
                    "morning": {
                        "time": "06:10",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:25",
                        "departure": ""
                    }
                },
                "5": {
                    "morning": {
                        "time": "06:40",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:55",
                        "departure": ""
                    }
                },
                "6": {
                    "morning": {
                        "time": "07:10",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:05",
                        "departure": ""
                    }
                }
            }
        },
        "sunday_holiday": {
            "label": "일요일(공휴일)",
            "fleet_count": 6,
            "orders": {
                "1": {
                    "morning": {
                        "time": "05:00",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:40",
                        "departure": ""
                    }
                },
                "2": {
                    "morning": {
                        "time": "05:25",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:15",
                        "departure": ""
                    }
                },
                "3": {
                    "morning": {
                        "time": "05:50",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:50",
                        "departure": ""
                    }
                },
                "4": {
                    "morning": {
                        "time": "06:10",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:25",
                        "departure": ""
                    }
                },
                "5": {
                    "morning": {
                        "time": "06:40",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:55",
                        "departure": ""
                    }
                },
                "6": {
                    "morning": {
                        "time": "07:10",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:05",
                        "departure": ""
                    }
                }
            }
        }
    },
    "급행97": {
        "weekday": {
            "label": "평일",
            "fleet_count": 10,
            "orders": {
                "1": {
                    "morning": {
                        "time": "05:00",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "12:00",
                        "departure": ""
                    }
                },
                "2": {
                    "morning": {
                        "time": "05:20",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "12:20",
                        "departure": ""
                    }
                },
                "3": {
                    "morning": {
                        "time": "05:40",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "12:40",
                        "departure": ""
                    }
                },
                "4": {
                    "morning": {
                        "time": "06:00",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "13:00",
                        "departure": ""
                    }
                },
                "5": {
                    "morning": {
                        "time": "06:19",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "13:20",
                        "departure": ""
                    }
                },
                "6": {
                    "morning": {
                        "time": "06:38",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "13:40",
                        "departure": ""
                    }
                },
                "7": {
                    "morning": {
                        "time": "06:55",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:00",
                        "departure": ""
                    }
                },
                "8": {
                    "morning": {
                        "time": "07:15",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:20",
                        "departure": ""
                    }
                },
                "9": {
                    "morning": {
                        "time": "07:35",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:40",
                        "departure": ""
                    }
                },
                "10": {
                    "morning": {
                        "time": "07:55",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:00",
                        "departure": ""
                    }
                }
            }
        },
        "saturday": {
            "label": "토요일",
            "fleet_count": 8,
            "orders": {
                "1": {
                    "morning": {
                        "time": "05:00",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "12:00",
                        "departure": ""
                    }
                },
                "2": {
                    "morning": {
                        "time": "05:25",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "12:28",
                        "departure": ""
                    }
                },
                "3": {
                    "morning": {
                        "time": "05:50",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "12:56",
                        "departure": ""
                    }
                },
                "4": {
                    "morning": {
                        "time": "06:15",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "13:24",
                        "departure": ""
                    }
                },
                "5": {
                    "morning": {
                        "time": "06:40",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "13:52",
                        "departure": ""
                    }
                },
                "6": {
                    "morning": {
                        "time": "07:05",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:20",
                        "departure": ""
                    }
                },
                "7": {
                    "morning": {
                        "time": "07:30",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:48",
                        "departure": ""
                    }
                },
                "8": {
                    "morning": {
                        "time": "07:57",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:16",
                        "departure": ""
                    }
                }
            }
        },
        "sunday_holiday": {
            "label": "일요일(공휴일)",
            "fleet_count": 7,
            "orders": {
                "1": {
                    "morning": {
                        "time": "05:00",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "12:10",
                        "departure": ""
                    }
                },
                "2": {
                    "morning": {
                        "time": "05:30",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "12:42",
                        "departure": ""
                    }
                },
                "3": {
                    "morning": {
                        "time": "06:00",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "13:14",
                        "departure": ""
                    }
                },
                "4": {
                    "morning": {
                        "time": "06:30",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "13:46",
                        "departure": ""
                    }
                },
                "5": {
                    "morning": {
                        "time": "07:00",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:18",
                        "departure": ""
                    }
                },
                "6": {
                    "morning": {
                        "time": "07:30",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:50",
                        "departure": ""
                    }
                },
                "7": {
                    "morning": {
                        "time": "08:00",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:22",
                        "departure": ""
                    }
                }
            }
        }
    },
    "30": {
        "weekday": {
            "label": "평일",
            "fleet_count": 33,
            "orders": {
                "1": {
                    "morning": {
                        "time": "04:40",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:09",
                        "departure": ""
                    }
                },
                "2": {
                    "morning": {
                        "time": "04:48",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:18",
                        "departure": ""
                    }
                },
                "3": {
                    "morning": {
                        "time": "04:56",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:27",
                        "departure": ""
                    }
                },
                "4": {
                    "morning": {
                        "time": "05:03",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:36",
                        "departure": ""
                    }
                },
                "5": {
                    "morning": {
                        "time": "05:10",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:45",
                        "departure": ""
                    }
                },
                "6": {
                    "morning": {
                        "time": "05:17",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:54",
                        "departure": ""
                    }
                },
                "7": {
                    "morning": {
                        "time": "05:24",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:03",
                        "departure": ""
                    }
                },
                "8": {
                    "morning": {
                        "time": "05:31",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:12",
                        "departure": ""
                    }
                },
                "9": {
                    "morning": {
                        "time": "05:37",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:21",
                        "departure": ""
                    }
                },
                "10": {
                    "morning": {
                        "time": "05:43",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:30",
                        "departure": ""
                    }
                },
                "11": {
                    "morning": {
                        "time": "05:49",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:39",
                        "departure": ""
                    }
                },
                "12": {
                    "morning": {
                        "time": "05:55",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:48",
                        "departure": ""
                    }
                },
                "13": {
                    "morning": {
                        "time": "06:01",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:57",
                        "departure": ""
                    }
                },
                "14": {
                    "morning": {
                        "time": "06:07",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:06",
                        "departure": ""
                    }
                },
                "15": {
                    "morning": {
                        "time": "06:13",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:15",
                        "departure": ""
                    }
                },
                "16": {
                    "morning": {
                        "time": "06:19",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:24",
                        "departure": ""
                    }
                },
                "17": {
                    "morning": {
                        "time": "06:25",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:33",
                        "departure": ""
                    }
                },
                "18": {
                    "morning": {
                        "time": "06:31",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:42",
                        "departure": ""
                    }
                },
                "19": {
                    "morning": {
                        "time": "06:38",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:51",
                        "departure": ""
                    }
                },
                "20": {
                    "morning": {
                        "time": "06:45",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "17:00",
                        "departure": ""
                    }
                },
                "21": {
                    "morning": {
                        "time": "06:52",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "17:09",
                        "departure": ""
                    }
                },
                "22": {
                    "morning": {
                        "time": "07:00",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "17:18",
                        "departure": ""
                    }
                },
                "23": {
                    "morning": {
                        "time": "07:09",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "17:27",
                        "departure": ""
                    }
                },
                "24": {
                    "morning": {
                        "time": "05:00",
                        "departure": "부평"
                    },
                    "afternoon": {
                        "time": "12:29",
                        "departure": ""
                    }
                },
                "25": {
                    "morning": {
                        "time": "05:13",
                        "departure": "부평"
                    },
                    "afternoon": {
                        "time": "12:39",
                        "departure": ""
                    }
                },
                "26": {
                    "morning": {
                        "time": "05:26",
                        "departure": "부평"
                    },
                    "afternoon": {
                        "time": "12:50",
                        "departure": ""
                    }
                },
                "27": {
                    "morning": {
                        "time": "05:00",
                        "departure": "송내"
                    },
                    "afternoon": {
                        "time": "13:00",
                        "departure": ""
                    }
                },
                "28": {
                    "morning": {
                        "time": "05:13",
                        "departure": "송내"
                    },
                    "afternoon": {
                        "time": "13:10",
                        "departure": ""
                    }
                },
                "29": {
                    "morning": {
                        "time": "05:26",
                        "departure": "송내"
                    },
                    "afternoon": {
                        "time": "13:20",
                        "departure": ""
                    }
                },
                "30": {
                    "morning": {
                        "time": "05:39",
                        "departure": "송내"
                    },
                    "afternoon": {
                        "time": "13:30",
                        "departure": ""
                    }
                },
                "31": {
                    "morning": {
                        "time": "05:52",
                        "departure": "송내"
                    },
                    "afternoon": {
                        "time": "13:40",
                        "departure": ""
                    }
                },
                "32": {
                    "morning": {
                        "time": "06:05",
                        "departure": "송내"
                    },
                    "afternoon": {
                        "time": "13:50",
                        "departure": ""
                    }
                },
                "33": {
                    "morning": {
                        "time": "06:18",
                        "departure": "송내"
                    },
                    "afternoon": {
                        "time": "14:00",
                        "departure": ""
                    }
                }
            }
        },
        "saturday": {
            "label": "토요일",
            "fleet_count": 25,
            "orders": {
                "1": {
                    "morning": {
                        "time": "04:40",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:09",
                        "departure": ""
                    }
                },
                "2": {
                    "morning": {
                        "time": "04:50",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:18",
                        "departure": ""
                    }
                },
                "3": {
                    "morning": {
                        "time": "05:00",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:27",
                        "departure": ""
                    }
                },
                "4": {
                    "morning": {
                        "time": "05:10",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:36",
                        "departure": ""
                    }
                },
                "5": {
                    "morning": {
                        "time": "05:20",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:45",
                        "departure": ""
                    }
                },
                "6": {
                    "morning": {
                        "time": "05:30",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:54",
                        "departure": ""
                    }
                },
                "7": {
                    "morning": {
                        "time": "05:40",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:03",
                        "departure": ""
                    }
                },
                "8": {
                    "morning": {
                        "time": "05:50",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:12",
                        "departure": ""
                    }
                },
                "9": {
                    "morning": {
                        "time": "06:00",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:21",
                        "departure": ""
                    }
                },
                "10": {
                    "morning": {
                        "time": "06:10",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:30",
                        "departure": ""
                    }
                },
                "11": {
                    "morning": {
                        "time": "06:20",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:39",
                        "departure": ""
                    }
                },
                "12": {
                    "morning": {
                        "time": "06:30",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:48",
                        "departure": ""
                    }
                },
                "13": {
                    "morning": {
                        "time": "06:40",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:57",
                        "departure": ""
                    }
                },
                "14": {
                    "morning": {
                        "time": "06:50",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:06",
                        "departure": ""
                    }
                },
                "15": {
                    "morning": {
                        "time": "07:00",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:15",
                        "departure": ""
                    }
                },
                "16": {
                    "morning": {
                        "time": "05:00",
                        "departure": "부평"
                    },
                    "afternoon": {
                        "time": "16:24",
                        "departure": ""
                    }
                },
                "17": {
                    "morning": {
                        "time": "05:13",
                        "departure": "부평"
                    },
                    "afternoon": {
                        "time": "16:33",
                        "departure": ""
                    }
                },
                "18": {
                    "morning": {
                        "time": "05:26",
                        "departure": "부평"
                    },
                    "afternoon": {
                        "time": "16:42",
                        "departure": ""
                    }
                },
                "19": {
                    "morning": {
                        "time": "05:00",
                        "departure": "송내"
                    },
                    "afternoon": {
                        "time": "16:51",
                        "departure": ""
                    }
                },
                "20": {
                    "morning": {
                        "time": "05:13",
                        "departure": "송내"
                    },
                    "afternoon": {
                        "time": "17:00",
                        "departure": ""
                    }
                },
                "21": {
                    "morning": {
                        "time": "05:26",
                        "departure": "송내"
                    },
                    "afternoon": {
                        "time": "17:09",
                        "departure": ""
                    }
                },
                "22": {
                    "morning": {
                        "time": "05:39",
                        "departure": "송내"
                    },
                    "afternoon": {
                        "time": "17:18",
                        "departure": ""
                    }
                },
                "23": {
                    "morning": {
                        "time": "05:52",
                        "departure": "송내"
                    },
                    "afternoon": {
                        "time": "17:27",
                        "departure": ""
                    }
                },
                "24": {
                    "morning": {
                        "time": "06:05",
                        "departure": "송내"
                    },
                    "afternoon": {
                        "time": "12:29",
                        "departure": ""
                    }
                },
                "25": {
                    "morning": {
                        "time": "06:18",
                        "departure": "송내"
                    },
                    "afternoon": {
                        "time": "12:39",
                        "departure": ""
                    }
                }
            }
        },
        "sunday_holiday": {
            "label": "일요일(공휴일)",
            "fleet_count": 22,
            "orders": {
                "1": {
                    "morning": {
                        "time": "04:40",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:30",
                        "departure": ""
                    }
                },
                "2": {
                    "morning": {
                        "time": "04:53",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "14:45",
                        "departure": ""
                    }
                },
                "3": {
                    "morning": {
                        "time": "05:06",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:00",
                        "departure": ""
                    }
                },
                "4": {
                    "morning": {
                        "time": "05:19",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:15",
                        "departure": ""
                    }
                },
                "5": {
                    "morning": {
                        "time": "05:32",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:30",
                        "departure": ""
                    }
                },
                "6": {
                    "morning": {
                        "time": "05:45",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "15:45",
                        "departure": ""
                    }
                },
                "7": {
                    "morning": {
                        "time": "05:58",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:00",
                        "departure": ""
                    }
                },
                "8": {
                    "morning": {
                        "time": "06:10",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:15",
                        "departure": ""
                    }
                },
                "9": {
                    "morning": {
                        "time": "06:22",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:30",
                        "departure": ""
                    }
                },
                "10": {
                    "morning": {
                        "time": "06:34",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "16:45",
                        "departure": ""
                    }
                },
                "11": {
                    "morning": {
                        "time": "06:46",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "17:00",
                        "departure": ""
                    }
                },
                "12": {
                    "morning": {
                        "time": "06:58",
                        "departure": ""
                    },
                    "afternoon": {
                        "time": "17:14",
                        "departure": ""
                    }
                },
                "13": {
                    "morning": {
                        "time": "05:00",
                        "departure": "부평"
                    },
                    "afternoon": {
                        "time": "12:00",
                        "departure": ""
                    }
                },
                "14": {
                    "morning": {
                        "time": "05:13",
                        "departure": "부평"
                    },
                    "afternoon": {
                        "time": "12:15",
                        "departure": ""
                    }
                },
                "15": {
                    "morning": {
                        "time": "05:26",
                        "departure": "부평"
                    },
                    "afternoon": {
                        "time": "12:30",
                        "departure": ""
                    }
                },
                "16": {
                    "morning": {
                        "time": "05:00",
                        "departure": "송내"
                    },
                    "afternoon": {
                        "time": "12:45",
                        "departure": ""
                    }
                },
                "17": {
                    "morning": {
                        "time": "05:13",
                        "departure": "송내"
                    },
                    "afternoon": {
                        "time": "13:00",
                        "departure": ""
                    }
                },
                "18": {
                    "morning": {
                        "time": "05:26",
                        "departure": "송내"
                    },
                    "afternoon": {
                        "time": "13:15",
                        "departure": ""
                    }
                },
                "19": {
                    "morning": {
                        "time": "05:39",
                        "departure": "송내"
                    },
                    "afternoon": {
                        "time": "13:30",
                        "departure": ""
                    }
                },
                "20": {
                    "morning": {
                        "time": "05:52",
                        "departure": "송내"
                    },
                    "afternoon": {
                        "time": "13:45",
                        "departure": ""
                    }
                },
                "21": {
                    "morning": {
                        "time": "06:05",
                        "departure": "송내"
                    },
                    "afternoon": {
                        "time": "14:00",
                        "departure": ""
                    }
                },
                "22": {
                    "morning": {
                        "time": "06:18",
                        "departure": "송내"
                    },
                    "afternoon": {
                        "time": "14:15",
                        "departure": ""
                    }
                }
            }
        }
    }
}


def normalize_route_number(value: Any) -> str:
    route = str(value or "").strip()
    return route[:-1].strip() if route.endswith("번") else route


def default_service_for_day_type(day_type: str) -> str:
    return {
        "weekday": SERVICE_WEEKDAY,
        "saturday": SERVICE_SATURDAY,
        "sunday": SERVICE_SUNDAY_HOLIDAY,
    }.get(day_type, "")


def available_services(route_number: Any) -> tuple[str, ...]:
    route = ROUTE_SCHEDULES.get(normalize_route_number(route_number), {})
    return tuple(key for key in SERVICE_LABELS if key in route)


def service_for_date(route_number: Any, day_type: str, saved_service: str = "") -> str:
    services = available_services(route_number)
    if saved_service in services:
        return saved_service
    default = default_service_for_day_type(day_type)
    return default if default in services else ""


def company_fleet_count(route_number: Any, service_type: str) -> int:
    try:
        return int(ROUTE_SCHEDULES[normalize_route_number(route_number)][service_type]["fleet_count"])
    except (KeyError, TypeError, ValueError):
        return 0


def lookup_schedule(route_number: Any, service_type: str, status: str, order_no: Any) -> dict[str, str] | None:
    shift = STATUS_TO_SHIFT.get(status)
    order = str(order_no or "").strip()
    if not shift or not order.isdigit():
        return None
    try:
        item = ROUTE_SCHEDULES[normalize_route_number(route_number)][service_type]["orders"][order][shift]
    except (KeyError, TypeError):
        return None
    if not isinstance(item, Mapping) or not item.get("time"):
        return None
    return {"time": str(item["time"]), "departure": str(item.get("departure", "") or "")}
