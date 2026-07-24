"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Calendar, ChevronLeft, ChevronRight, Clock, MapPin, User, Plus, Loader2 } from "lucide-react";

const weekDays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

const eventColors: Record<string, string> = {
  showing: "bg-amber-100 text-amber-700 border-amber-200",
  meeting: "bg-blue-100 text-blue-700 border-blue-200",
  "open-house": "bg-green-100 text-green-700 border-green-200",
  closing: "bg-emerald-100 text-emerald-700 border-emerald-200",
  inspection: "bg-purple-100 text-purple-700 border-purple-200",
};

type CalendarEvent = {
  id: string;
  title: string;
  day: number;
  time: string;
  type: string;
  location: string;
  client: string;
  status: string;
};

export default function CalendarPage() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentMonth, setCurrentMonth] = useState(() => {
    const now = new Date();
    return now.toLocaleDateString("en-US", { month: "long", year: "numeric" });
  });
  const [selectedDay, setSelectedDay] = useState(() => new Date().getDate());

  const now = new Date();
  const currentYear = now.getFullYear();
  const currentMonthIndex = now.getMonth();
  const daysInMonth = new Date(currentYear, currentMonthIndex + 1, 0).getDate();
  const firstDayOfWeek = new Date(currentYear, currentMonthIndex, 1).getDay();
  const today = now.getDate();

  useEffect(() => {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://realty-ai-api-production.up.railway.app";
    fetch(`${API_BASE}/api/v1/calendar/events`)
      .then((r) => r.json())
      .then((data) => setEvents(data.events || []))
      .catch(() => setEvents([]))
      .finally(() => setLoading(false));
  }, []);

  const dayEvents = events.filter((e) => e.day === selectedDay);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Calendar</h1>
          <p className="mt-1 text-sm text-gray-500">Manage your schedule and appointments</p>
        </div>
        <Button onClick={() => alert("To add an event, ask Athena to schedule a showing or meeting.")}>
          <Plus className="h-4 w-4" /> Add Event
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle>{currentMonth}</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-16">
                  <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                </div>
              ) : (
                <div className="grid grid-cols-7 gap-px">
                  {weekDays.map((d) => (
                    <div key={d} className="p-2 text-center text-xs font-medium text-gray-500">{d}</div>
                  ))}
                  {Array.from({ length: firstDayOfWeek }, (_, i) => (
                    <div key={`empty-${i}`} className="min-h-[80px] bg-gray-50/50" />
                  ))}
                  {Array.from({ length: daysInMonth }, (_, i) => {
                    const day = i + 1;
                    const isToday = day === today;
                    const isSelected = day === selectedDay;
                    const hasEvent = events.some((e) => e.day === day);
                    return (
                      <button
                        key={day}
                        onClick={() => setSelectedDay(day)}
                        className={`min-h-[80px] p-1.5 text-left transition-colors border border-gray-100 hover:bg-brand-50 ${
                          isSelected ? "bg-brand-50 ring-2 ring-brand-500" : ""
                        } ${isToday ? "bg-brand-50" : ""}`}
                      >
                        <span className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs ${
                          isToday ? "bg-brand-600 text-white font-bold" : "text-gray-700"
                        }`}>
                          {day}
                        </span>
                        {hasEvent && (
                          <div className="mt-1 space-y-0.5">
                            {events.filter((e) => e.day === day).slice(0, 2).map((e, idx) => (
                              <div key={idx} className="h-1.5 w-full rounded-full bg-brand-400" />
                            ))}
                            {events.filter((e) => e.day === day).length > 2 && (
                              <span className="text-[10px] text-gray-400">+more</span>
                            )}
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">
                Events — {currentMonth.split(" ")[0]} {selectedDay}, {currentYear}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
                </div>
              ) : dayEvents.length === 0 ? (
                <p className="py-8 text-center text-sm text-gray-400">No events scheduled</p>
              ) : (
                <div className="space-y-3">
                  {dayEvents.map((event) => (
                    <div key={event.id} className={`rounded-lg border p-3 ${eventColors[event.type] || "bg-gray-50"}`}>
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-sm font-semibold">{event.title}</p>
                        <Badge variant="outline" className="text-[10px]">{event.type}</Badge>
                      </div>
                      <div className="mt-2 space-y-1 text-xs opacity-80">
                        <div className="flex items-center gap-1.5">
                          <Clock className="h-3 w-3" />
                          <span>{event.time}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <MapPin className="h-3 w-3" />
                          <span>{event.location}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <User className="h-3 w-3" />
                          <span>{event.client}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}