import type { Metadata } from "next"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { CalendarDateRangePicker } from "@/components/date-range-picker"
import { MainNav } from "@/components/main-nav"
import { Overview } from "@/components/overview"
import { RecentEmails } from "@/components/recent-emails"
import { Search } from "@/components/search"
import TeamSwitcher from "@/components/team-switcher"
import { UserNav } from "@/components/user-nav"
import { TodoList } from "@/components/todo-list"
import { CustomTagsTable } from "@/components/custom-tags-table"

export const metadata: Metadata = {
  title: "Dashboard | AutoMail",
  description: "Manage your emails efficiently with AutoMail.",
}

export default function DashboardPage() {
  return (
    <>
      <div className="flex-col md:flex">
        <div className="border-b">
          <div className="flex h-16 items-center px-4">
            <TeamSwitcher />
            <MainNav className="mx-6" />
            <div className="ml-auto flex items-center space-x-4">
              <Search />
              <UserNav />
            </div>
          </div>
        </div>
        <div className="flex-1 space-y-4 p-8 pt-6">
          <div className="flex items-center justify-between space-y-2">
            <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
            <div className="flex items-center space-x-2">
              <CalendarDateRangePicker />
              <Button>Download</Button>
            </div>
          </div>
          <Tabs defaultValue="overview" className="space-y-4">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="analytics">Analytics</TabsTrigger>
              <TabsTrigger value="custom-tags">Custom Tags</TabsTrigger>
              <TabsTrigger value="notifications">Notifications</TabsTrigger>
            </TabsList>
            <TabsContent value="overview" className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Emails</CardTitle>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      className="h-4 w-4 text-muted-foreground"
                    >
                      <path d="M12 2v20M2 12h20" />
                    </svg>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">2,543</div>
                    <p className="text-xs text-muted-foreground">+20.1% from last month</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Auto-Labeled</CardTitle>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      className="h-4 w-4 text-muted-foreground"
                    >
                      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                      <circle cx="9" cy="7" r="4" />
                      <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
                    </svg>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">1,892</div>
                    <p className="text-xs text-muted-foreground">+180.1% from last month</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Auto-Responses</CardTitle>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      className="h-4 w-4 text-muted-foreground"
                    >
                      <rect width="20" height="14" x="2" y="5" rx="2" />
                      <path d="M2 10h20" />
                    </svg>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">432</div>
                    <p className="text-xs text-muted-foreground">+19% from last month</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Time Saved</CardTitle>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      className="h-4 w-4 text-muted-foreground"
                    >
                      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                    </svg>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">24.5 hrs</div>
                    <p className="text-xs text-muted-foreground">+201 minutes since last month</p>
                  </CardContent>
                </Card>
              </div>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                <Card className="col-span-4">
                  <CardHeader>
                    <CardTitle>Email Activity</CardTitle>
                  </CardHeader>
                  <CardContent className="pl-2">
                    <Overview />
                  </CardContent>
                </Card>
                <Card className="col-span-3">
                  <CardHeader>
                    <CardTitle>Recent Emails</CardTitle>
                    <CardDescription>You received 34 emails this week.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <RecentEmails />
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
            <TabsContent value="analytics" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Funds Used */}
                <Card className="col-span-1 md:col-span-2 lg:col-span-1">
                  <CardHeader>
                    <CardTitle>Funds Used</CardTitle>
                    <CardDescription>Financial data from your accounts</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="space-y-1">
                          <p className="text-sm font-medium leading-none">Marketing Budget</p>
                          <p className="text-sm text-muted-foreground">April 2025</p>
                        </div>
                        <div className="font-medium">$12,450 / $15,000</div>
                      </div>
                      <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                        <div className="bg-primary h-full rounded-full" style={{ width: "83%" }}></div>
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="space-y-1">
                          <p className="text-sm font-medium leading-none">Development Resources</p>
                          <p className="text-sm text-muted-foreground">April 2025</p>
                        </div>
                        <div className="font-medium">$8,230 / $10,000</div>
                      </div>
                      <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                        <div className="bg-primary h-full rounded-full" style={{ width: "82.3%" }}></div>
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="space-y-1">
                          <p className="text-sm font-medium leading-none">Operations</p>
                          <p className="text-sm text-muted-foreground">April 2025</p>
                        </div>
                        <div className="font-medium">$5,320 / $8,000</div>
                      </div>
                      <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                        <div className="bg-primary h-full rounded-full" style={{ width: "66.5%" }}></div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Reminders */}
                <Card className="col-span-1">
                  <CardHeader>
                    <CardTitle>Upcoming Meetings</CardTitle>
                    <CardDescription>Extracted from your emails</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-start space-x-4">
                        <div className="bg-primary/10 text-primary rounded-md p-2 w-12 h-12 flex flex-col items-center justify-center">
                          <span className="text-xs font-bold">APR</span>
                          <span className="text-lg font-bold">20</span>
                        </div>
                        <div className="space-y-1">
                          <p className="text-sm font-medium">Product Review</p>
                          <p className="text-xs text-muted-foreground">10:00 AM - 11:30 AM</p>
                          <p className="text-xs">with Design Team</p>
                        </div>
                      </div>

                      <div className="flex items-start space-x-4">
                        <div className="bg-primary/10 text-primary rounded-md p-2 w-12 h-12 flex flex-col items-center justify-center">
                          <span className="text-xs font-bold">APR</span>
                          <span className="text-lg font-bold">22</span>
                        </div>
                        <div className="space-y-1">
                          <p className="text-sm font-medium">Client Presentation</p>
                          <p className="text-xs text-muted-foreground">2:00 PM - 3:30 PM</p>
                          <p className="text-xs">with Acme Corp.</p>
                        </div>
                      </div>

                      <div className="flex items-start space-x-4">
                        <div className="bg-primary/10 text-primary rounded-md p-2 w-12 h-12 flex flex-col items-center justify-center">
                          <span className="text-xs font-bold">APR</span>
                          <span className="text-lg font-bold">25</span>
                        </div>
                        <div className="space-y-1">
                          <p className="text-sm font-medium">Team Sync</p>
                          <p className="text-xs text-muted-foreground">11:00 AM - 12:00 PM</p>
                          <p className="text-xs">Weekly standup</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Todo Checklist */}
                <Card className="col-span-1">
                  <CardHeader>
                    <CardTitle>Todo List</CardTitle>
                    <CardDescription>Tasks extracted from emails</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <TodoList />
                  </CardContent>
                </Card>

                {/* Auto Drafts */}
                <Card className="col-span-1 md:col-span-2 lg:col-span-3">
                  <CardHeader>
                    <CardTitle>Auto Drafts</CardTitle>
                    <CardDescription>AI-generated email responses ready to send</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="border rounded-lg p-4 hover:bg-accent transition-colors cursor-pointer">
                        <div className="flex items-center justify-between mb-2">
                          <div className="font-medium">Re: Project Timeline Update</div>
                          <div className="text-xs text-muted-foreground">To: Sarah Johnson</div>
                        </div>
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          Thanks for the update on the project timeline. I've reviewed the changes and agree with the
                          new milestones. Let's discuss the resource allocation during our next meeting...
                        </p>
                        <div className="flex justify-end mt-2 space-x-2">
                          <Button variant="outline" size="sm">
                            Edit
                          </Button>
                          <Button size="sm">Send</Button>
                        </div>
                      </div>

                      <div className="border rounded-lg p-4 hover:bg-accent transition-colors cursor-pointer">
                        <div className="flex items-center justify-between mb-2">
                          <div className="font-medium">Re: Quarterly Budget Review</div>
                          <div className="text-xs text-muted-foreground">To: Finance Team</div>
                        </div>
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          I've reviewed the Q1 budget report and have a few questions about the marketing expense
                          allocation. Could we schedule a quick call to discuss the variances in the digital advertising
                          spend...
                        </p>
                        <div className="flex justify-end mt-2 space-x-2">
                          <Button variant="outline" size="sm">
                            Edit
                          </Button>
                          <Button size="sm">Send</Button>
                        </div>
                      </div>

                      <div className="border rounded-lg p-4 hover:bg-accent transition-colors cursor-pointer">
                        <div className="flex items-center justify-between mb-2">
                          <div className="font-medium">Re: Client Meeting Follow-up</div>
                          <div className="text-xs text-muted-foreground">To: Michael Chen, Client Success</div>
                        </div>
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          Thank you for organizing yesterday's client meeting. I've attached the action items we
                          discussed and assigned team members to each task. Let's reconvene next week to check on
                          progress...
                        </p>
                        <div className="flex justify-end mt-2 space-x-2">
                          <Button variant="outline" size="sm">
                            Edit
                          </Button>
                          <Button size="sm">Send</Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
            <TabsContent value="custom-tags" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Custom Tags</CardTitle>
                  <CardDescription>Manage your custom email tags and labels</CardDescription>
                </CardHeader>
                <CardContent>
                  <CustomTagsTable />
                </CardContent>
              </Card>
            </TabsContent>
            <TabsContent value="notifications">
              <Card>
                <CardHeader>
                  <CardTitle>Notifications</CardTitle>
                  <CardDescription>View and manage your notification settings</CardDescription>
                </CardHeader>
                <CardContent>
                  <p>You have no new notifications.</p>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </>
  )
}
