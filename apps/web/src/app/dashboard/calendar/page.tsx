"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Calendar,
  ChevronLeft,
  ChevronRight,
  Clock,
  MapPin,
  User,
  Plus,
  Loader2,
  Bell,
  BellOff,
  Trash2,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

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
  month: number;
  year: number;
  time: string;
  type: string;
  location: string;
  client: string;
  status: string;
};

type Reminder = {
  id: string;
  event_id: string;
  title: string;
  description: string;
  remind_at: string;
  status: string;
  created_at: string;
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined" && window.location.hostname === "localhost"
    ? "http://185.80.130.197:8000"
    : "https://realty-api.indicationsmedia.com");

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export default function CalendarPage() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [loading, setLoading] = useState(true);
  const [reminderLoading, setReminderLoading] = useState(true);
  const [year, setYear] = useState(() => new Date().getFullYear());
  const [monthIndex, setMonthIndex] = useState(() => new Date().getMonth());
  const [selectedDay, setSelectedDay] = useState(() => new Date().getDate());
  const [showReminderForm, setShowReminderForm] = useState(false);
  const [reminderEventId, setReminderEventId] = useState("");
  const [reminderTitle, setReminderTitle] = useState("");
  const [reminderDesc, setReminderDesc] = useState("");
  const [reminderTime, setReminderTime] = useState("");
  const [dismissingId, setDismissingId] = useState<string | null>(null);

  const today = new Date();
  const isCurrentMonth =
    year === today.getFullYear() && monthIndex === today.getMonth();

  // ── Month helpers ──────────────────────────────────────────────

  const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();
  const firstDayOfWeek = new Date(year, monthIndex, 1).getDay();

  const goToPrevMonth = () => {
    if (monthIndex === 0) {
      setYear((y) => y - 1);
      setMonthIndex(11);
    } else {
      setMonthIndex((m) => m - 1);
    }
    setSelectedDay(1);
  };

  const goToNextMonth = () => {
    if (monthIndex === 11) {
      setYear((y) => y + 1);
      setMonthIndex(0);
    } else {
      setMonthIndex((m) => m + 1);
    }
    setSelectedDay(1);
  };

  const goToToday = () => {
    setYear(today.getFullYear());
    setMonthIndex(today.getMonth());
    setSelectedDay(today.getDate());
  };

  // ── Fetch events ──────────────────────────────────────────────

  const fetchEvents = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/calendar/events`);
      const data = await res.json();
      const parsed: CalendarEvent[] = (data.events || []).map((e: any) => {
        const dt = new Date();
        let d = e.day || dt.getDate();
        let m = dt.getMonth();
        let y = dt.getFullYear();
        if (e.start_time) {
          const p = new Date(e.start_time);
          if (!isNaN(p.getTime())) {
            d = p.getDate();
            m = p.getMonth();
            y = p.getFullYear();
          }
        }
        return { ...e, day: d, month: m, year: y };
      });
      setEvents(parsed);
    } catch {
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // ── Fetch reminders ───────────────────────────────────────────

  const fetchReminders = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/calendar/reminders`);
      const data = await res.json();
      setReminders(data.reminders || []);
    } catch {
      setReminders([]);
    } finally {
      setReminderLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEvents();
    fetchReminders();
  }, [fetchEvents, fetchReminders]);

  // ── Filters ──────────────────────────────────────────────────

  const monthEvents = events.filter(
    (e) => e.month === monthIndex && e.year === year
  );

  const dayEvents = events.filter(
    (e) =>
      e.day === selectedDay &&
      e.month === monthIndex &&
      e.year === year
  );

  // ── Reminder actions ──────────────────────────────────────────

  const openReminderForm = (eventId: string, title: string) => {
    setReminderEventId(eventId);
    setReminderTitle(`Reminder: ${title}`);
    setReminderDesc("");
    const defaultTime = new Date();
    defaultTime.setHours(defaultTime.getHours() + 1, 0, 0, 0);
    setReminderTime(defaultTime.toISOString().slice(0, 16));
    setShowReminderForm(true);
  };

  const submitReminder = async () => {
    if (!reminderTime) return;
    try {
      const remindAt = new Date(reminderTime).toISOString();
      await fetch(`${API_BASE}/api/v1/calendar/reminders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_id: reminderEventId,
          title: reminderTitle,
          description: reminderDesc,
          remind_at: remindAt,
        }),
      });
      setShowReminderForm(false);
      fetchReminders();
    } catch (err) {
      console.error("Failed to create reminder:", err);
    }
  };

  const dismissReminder = async (id: string) => {
    setDismissingId(id);
    try {
      await fetch(`${API_BASE}/api/v1/calendar/reminders/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "dismissed" }),
      });
      setReminders((prev) => prev.filter((r) => r.id !== id));
    } catch (err) {
      console.error("Failed to dismiss reminder:", err);
    } finally {
      setDismissingId(null);
    }
  };

  const deleteReminder = async (id: string) => {
    try {
      await fetch(`${API_BASE}/api/v1/calendar/reminders/${id}`, {
        method: "DELETE",
      });
      setReminders((prev) => prev.filter((r) => r.id !== id));
    } catch (err) {
      console.error("Failed to delete reminder:", err);
    }
  };

  // ── Render helpers ────────────────────────────────────────────

  const formatDate = (iso: string) => {
    try {
      const d = new Date(iso);
      return d.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      });
    } catch {
      return iso;
    }
  };

  const timeUntil = (iso: string) => {
    try {
      const diff = new Date(iso).getTime() - Date.now();
      if (diff < 0) return "Overdue";
      const hrs = Math.floor(diff / 3600000);
      const mins = Math.floor((diff % 3600000) / 60000);
      if (hrs > 48) return `${Math.floor(hrs / 24)}d ${hrs % 24}h`;
      if (hrs > 0) return `${hrs}h ${mins}m`;
      return `${mins}m`;
    } catch {
      return "";
    }
  };

  const reminderBadge = (r: Reminder) => {
    try {
      const diff = new Date(r.remind_at).getTime() - Date.now();
      if (diff < 0) return "bg-red-100 text-red-700 border-red-200";
      if (diff < 3600000) return "bg-yellow-100 text-yellow-700 border-yellow-200";
      return "bg-green-100 text-green-700 border-green-200";
    } catch {
      return "bg-gray-100 text-gray-700";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Calendar</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your schedule and appointments
          </p>
        </div>
        <Button
          onClick={() =>
            alert("To add an event, ask Athena to schedule a showing or meeting.")
          }
        >
          <Plus className="h-4 w-4" /> Add Event
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Calendar Grid */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={goToPrevMonth}
                    className="h-8 w-8 p-0"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <CardTitle className="text-lg min-w-[200px] text-center">
                    {MONTHS[monthIndex]} {year}
                  </CardTitle>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={goToNextMonth}
                    className="h-8 w-8 p-0"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
                {!isCurrentMonth && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={goToToday}
                    className="text-xs text-brand-600"
                  >
                    Today
                  </Button>
                )}
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
                    <div
                      key={d}
                      className="p-2 text-center text-xs font-medium text-gray-500"
                    >
                      {d}
                    </div>
                  ))}
                  {Array.from({ length: firstDayOfWeek }, (_, i) => (
                    <div
                      key={`empty-${i}`}
                      className="min-h-[80px] bg-gray-50/50"
                    />
                  ))}
                  {Array.from({ length: daysInMonth }, (_, i) => {
                    const day = i + 1;
                    const isToday =
                      day === today.getDate() &&
                      monthIndex === today.getMonth() &&
                      year === today.getFullYear();
                    const isSelected = day === selectedDay;
                    const dayEventsList = monthEvents.filter(
                      (e) => e.day === day
                    );
                    const hasEvent = dayEventsList.length > 0;
                    return (
                      <button
                        key={day}
                        onClick={() => setSelectedDay(day)}
                        className={`min-h-[80px] p-1.5 text-left transition-colors border border-gray-100 hover:bg-brand-50 ${
                          isSelected ? "bg-brand-50 ring-2 ring-brand-500" : ""
                        } ${isToday ? "bg-brand-50" : ""}`}
                      >
                        <span
                          className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs ${
                            isToday
                              ? "bg-brand-600 text-white font-bold"
                              : "text-gray-700"
                          }`}
                        >
                          {day}
                        </span>
                        {hasEvent && (
                          <div className="mt-1 space-y-0.5">
                            {dayEventsList.slice(0, 3).map((e, idx) => (
                              <div
                                key={idx}
                                className="h-1.5 w-full rounded-full bg-brand-400"
                              />
                            ))}
                            {dayEventsList.length > 3 && (
                              <span className="text-[10px] text-gray-400">
                                +{dayEventsList.length - 3} more
                              </span>
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

        {/* Right Panel */}
        <div className="space-y-4">
          {/* Day Events */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">
                Events — {MONTHS[monthIndex]} {selectedDay}, {year}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
                </div>
              ) : dayEvents.length === 0 ? (
                <p className="py-8 text-center text-sm text-gray-400">
                  No events scheduled
                </p>
              ) : (
                <div className="space-y-3">
                  {dayEvents.map((event) => (
                    <div
                      key={event.id}
                      className={`rounded-lg border p-3 ${
                        eventColors[event.type] || "bg-gray-50"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-sm font-semibold">{event.title}</p>
                        <Badge
                          variant="outline"
                          className="text-[10px]"
                        >
                          {event.type}
                        </Badge>
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
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          openReminderForm(event.id, event.title)
                        }
                        className="mt-2 h-7 text-xs gap-1 text-brand-600"
                      >
                        <Bell className="h-3 w-3" /> Set Reminder
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Reminders Panel */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Bell className="h-4 w-4 text-brand-600" />
                  Upcoming Reminders
                </CardTitle>
                <Badge variant="secondary" className="text-[10px]">
                  {reminders.length}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {reminderLoading ? (
                <div className="flex items-center justify-center py-6">
                  <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
                </div>
              ) : reminders.length === 0 ? (
                <div className="py-6 text-center">
                  <BellOff className="h-8 w-8 text-gray-300 mx-auto mb-2" />
                  <p className="text-sm text-gray-400">No pending reminders</p>
                  <p className="text-xs text-gray-300 mt-1">
                    Click &quot;Set Reminder&quot; on any event to add one
                  </p>
                </div>
              ) : (
                <div className="space-y-2 max-h-[300px] overflow-y-auto">
                  {reminders.map((r) => (
                    <div
                      key={r.id}
                      className={`rounded-lg border p-2.5 text-xs ${reminderBadge(
                        r
                      )}`}
                    >
                      <div className="flex items-start justify-between gap-1">
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold truncate">{r.title}</p>
                          {r.description && (
                            <p className="mt-0.5 opacity-80 truncate">
                              {r.description}
                            </p>
                          )}
                          <p className="mt-1 font-medium">
                            {formatDate(r.remind_at)}
                            <span className="ml-1 opacity-70">
                              ({timeUntil(r.remind_at)})
                            </span>
                          </p>
                        </div>
                        <div className="flex gap-1 flex-shrink-0">
                          <button
                            onClick={() => dismissReminder(r.id)}
                            disabled={dismissingId === r.id}
                            className="p-1 rounded hover:bg-white/50 transition-colors"
                            title="Dismiss"
                          >
                            <CheckCircle2 className="h-3.5 w-3.5" />
                          </button>
                          <button
                            onClick={() => deleteReminder(r.id)}
                            className="p-1 rounded hover:bg-white/50 transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
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

      {/* Reminder Form Modal */}
      {showReminderForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Bell className="h-5 w-5 text-brand-600" />
                Set Reminder
              </h3>
              <button
                onClick={() => setShowReminderForm(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Title
                </label>
                <input
                  type="text"
                  value={reminderTitle}
                  onChange={(e) => setReminderTitle(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={reminderDesc}
                  onChange={(e) => setReminderDesc(e.target.value)}
                  rows={2}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Remind at
                </label>
                <input
                  type="datetime-local"
                  value={reminderTime}
                  onChange={(e) => setReminderTime(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  variant="outline"
                  onClick={() => setShowReminderForm(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button onClick={submitReminder} className="flex-1">
                  <Bell className="h-4 w-4 mr-1" /> Set Reminder
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
