import VSA

#print(VSA.Auth.GetToken())
print(VSA.AgentProcedures.List())
print(VSA.Agents.Find("$filter=LastLoggedInUser eq 'Tanner'"))
print(VSA.AgentProcedures.RunNow(439533397247945, 3150151))
print(VSA.Agents.GetAllAlarms(returnAll="false"))
closealarm = VSA.Agents.CloseAlarm(124605)

assert(closealarm == 0)