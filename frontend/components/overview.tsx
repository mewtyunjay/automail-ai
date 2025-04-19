"use client"

import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis } from "recharts"

const data = [
  {
    name: "Mon",
    total: 42,
  },
  {
    name: "Tue",
    total: 38,
  },
  {
    name: "Wed",
    total: 64,
  },
  {
    name: "Thu",
    total: 43,
  },
  {
    name: "Fri",
    total: 57,
  },
  {
    name: "Sat",
    total: 29,
  },
  {
    name: "Sun",
    total: 22,
  },
]

export function Overview() {
  return (
    <ResponsiveContainer width="100%" height={350}>
      <BarChart data={data}>
        <XAxis dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
        <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}`} />
        <Bar dataKey="total" fill="currentColor" radius={[4, 4, 0, 0]} className="fill-primary" />
      </BarChart>
    </ResponsiveContainer>
  )
}
