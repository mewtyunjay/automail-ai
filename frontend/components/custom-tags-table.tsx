"use client"

import { useState } from "react"
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Badge } from "@/components/ui/badge"
import { Edit, MoreHorizontal, Plus, Trash2 } from "lucide-react"

// Initial tags data
const initialTags = [
  {
    id: "1",
    name: "Important",
    description: "High priority emails that need immediate attention",
    color: "red",
    count: 24,
  },
  {
    id: "2",
    name: "Work",
    description: "All work-related emails and communications",
    color: "blue",
    count: 156,
  },
  {
    id: "3",
    name: "Personal",
    description: "Personal emails from friends and family",
    color: "green",
    count: 43,
  },
  {
    id: "4",
    name: "Finance",
    description: "Bills, invoices, and financial statements",
    color: "yellow",
    count: 18,
  },
  {
    id: "5",
    name: "Travel",
    description: "Flight confirmations, hotel bookings, and itineraries",
    color: "purple",
    count: 7,
  },
  {
    id: "6",
    name: "Shopping",
    description: "Order confirmations and shipping notifications",
    color: "orange",
    count: 32,
  },
  {
    id: "7",
    name: "Social",
    description: "Notifications from social media platforms",
    color: "pink",
    count: 89,
  },
]

// Color mapping for badges
const colorMap: Record<string, string> = {
  red: "bg-red-100 text-red-800 hover:bg-red-100",
  blue: "bg-blue-100 text-blue-800 hover:bg-blue-100",
  green: "bg-green-100 text-green-800 hover:bg-green-100",
  yellow: "bg-yellow-100 text-yellow-800 hover:bg-yellow-100",
  purple: "bg-purple-100 text-purple-800 hover:bg-purple-100",
  orange: "bg-orange-100 text-orange-800 hover:bg-orange-100",
  pink: "bg-pink-100 text-pink-800 hover:bg-pink-100",
}

export function CustomTagsTable() {
  const [tags, setTags] = useState(initialTags)
  const [searchQuery, setSearchQuery] = useState("")

  // Filter tags based on search query
  const filteredTags = tags.filter(
    (tag) =>
      tag.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tag.description.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="relative w-full max-w-sm">
          <Input
            placeholder="Search tags..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full"
          />
        </div>
        <Button className="ml-auto">
          <Plus className="mr-2 h-4 w-4" /> Add New Tag
        </Button>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableCaption>A list of your custom email tags.</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[200px]">Tag Name</TableHead>
              <TableHead>Description</TableHead>
              <TableHead className="text-right">Email Count</TableHead>
              <TableHead className="w-[70px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredTags.map((tag) => (
              <TableRow key={tag.id}>
                <TableCell className="font-medium">
                  <div className="flex items-center space-x-2">
                    <Badge variant="outline" className={colorMap[tag.color]}>
                      {tag.name}
                    </Badge>
                  </div>
                </TableCell>
                <TableCell>{tag.description}</TableCell>
                <TableCell className="text-right">{tag.count}</TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" className="h-8 w-8 p-0">
                        <span className="sr-only">Open menu</span>
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuLabel>Actions</DropdownMenuLabel>
                      <DropdownMenuItem>
                        <Edit className="mr-2 h-4 w-4" /> Edit
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem className="text-destructive">
                        <Trash2 className="mr-2 h-4 w-4" /> Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
