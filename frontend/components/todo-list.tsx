"use client"

import { useState } from "react"

// Initial todo items
const initialTodos = [
  {
    id: "todo-1",
    text: "Review Q1 financial report",
    dueDate: "Due Apr 21",
    completed: false,
  },
  {
    id: "todo-2",
    text: "Send project proposal to client",
    dueDate: "Completed Apr 18",
    completed: true,
  },
  {
    id: "todo-3",
    text: "Prepare presentation slides",
    dueDate: "Due Apr 22",
    completed: false,
  },
  {
    id: "todo-4",
    text: "Schedule team building event",
    dueDate: "Due Apr 30",
    completed: false,
  },
  {
    id: "todo-5",
    text: "Follow up with marketing team",
    dueDate: "Due Apr 24",
    completed: false,
  },
]

export function TodoList() {
  // State to track todo items
  const [todos, setTodos] = useState(initialTodos)

  // Handle checkbox change
  const handleTodoChange = (id: string) => {
    setTodos(
      todos.map((todo) => {
        if (todo.id === id) {
          return { ...todo, completed: !todo.completed }
        }
        return todo
      }),
    )
  }

  return (
    <div className="space-y-4">
      {todos.map((todo) => (
        <div key={todo.id} className="flex items-start space-x-2">
          <div className="min-w-4 pt-1">
            <input
              type="checkbox"
              className="rounded-sm"
              id={todo.id}
              checked={todo.completed}
              onChange={() => handleTodoChange(todo.id)}
            />
          </div>
          <div className="space-y-1 flex-1">
            <label
              htmlFor={todo.id}
              className={`text-sm font-medium ${todo.completed ? "line-through text-muted-foreground" : ""}`}
            >
              {todo.text}
            </label>
            <p className="text-xs text-muted-foreground">{todo.dueDate}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
