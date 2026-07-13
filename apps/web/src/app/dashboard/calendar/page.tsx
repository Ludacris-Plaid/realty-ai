"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Calendar, ChevronLeft, ChevronRight, Clock, MapPin, User, Plus } from "lucide-react";

const weekDays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

const events = [
  { day: 13, title: "Property Showing - 123 Main St", time: "10:00 AM", type: "showing", location: "123 Main St, Edmonton", client: "John Smith" },
  { day: 13, title: "Client Meeting - Sarah Johnson", time: "2:00 PM", type: "meeting", location: "Office", client: "Sarah Johnson" },
  { day: 14, title: "Open House - 456 Oak Ave", time: "12:00 PM", type: "open-house", location: "456 Oak Ave, Edmonton", client: "Public" },
  { day: 15, title: "Listing Signing - Mike Chen", time: "11:00 AM", type: "closing", location: "Office", client: "Mike Chen" },
  { day: 16, title: "Inspection - 789 Pine Cres", time: "9:00 AM", type: "inspection", location: "789 Pine Cres, Edmonton", client: "Emily Davis" },
  { day: 18, title: "Broker Meeting", time: "8:00 AM", type: "meeting", location: "Conference Room", client: "Team" },
];

const eventColors: Record<string, string> = {
  showing: "bg-blue-100 text-blue-700 border-blue-200",
  meeting: "bg-purple-100 text-purple-700 border-purple-200",
  "open-house": "bg-green-100 text-green-700 border-green-200",
  closing: "bg-emerald-100 text-emerald-700 border-emerald-200",
  inspection: "bg-amber-100 text-amber-700 border-amber-200",
};

export default function CalendarPage() {
  const [currentMonth, setCurrentMonth] = useState("July 2026");
  const [selectedDay, setSelectedDay] = useState(13);

  const daysInMonth = 31;
  const firstDayOfWeek = 3; // July 2026 starts on Wednesday
  const today = 12;

  const dayEvents = events.filter((e) => e.day === selectedDay);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Calendar</h1>
          <p className="mt-1 text-sm text-gray-500">Manage your schedule and appointments</p>
        </div>
        <Button>
          <Plus className="h-4 w-4" /> Add Event
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle>{currentMonth}</CardTitle>
                <div className="flex gap-1">
                  <Button variant="ghost" size="sm"><ChevronLeft className="h-4 w-4" /></Button>
                  <Button variant="ghost" size="sm">Today</Button>
                  <Button variant="ghost" size="sm"><ChevronRight className="h-4 w-4" /></Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
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
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">
                Events for July {selectedDay}, 2026
              </CardTitle>
            </CardHeader>
            <CardContent>
              {dayEvents.length === 0 ? (
                <p className="py-8 text-center text-sm text-gray-400">No events scheduled</p>
              ) : (
                <div className="space-y-3">
                  {dayEvents.map((event, i) => (
                    <div key={i} className={`rounded-lg border p-3 ${eventColors[event.type] || "bg-gray-50"}`}>
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
