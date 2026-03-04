"use client";
import { useEffect, useState } from "react";
import { getOrgChart } from "@/lib/api";
import type { Department, Employee } from "@/lib/types";

export default function OrgPage() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);

  useEffect(() => {
    getOrgChart()
      .then((data) => {
        setDepartments(data.departments);
        setEmployees(data.employees);
      })
      .catch(() => {});
  }, []);

  const rootDept = departments.find((d) => d.parent_id === null || d.parent_id === undefined);
  const childDepts = departments.filter((d) => d.parent_id !== null && d.parent_id !== undefined);
  const getEmployees = (deptId: number) => employees.filter((e) => e.department_id === deptId);

  return (
    <div>
      <h2 className="text-xl font-semibold text-white mb-6">조직도</h2>

      {/* Root department */}
      {rootDept && (
        <div className="text-center mb-8">
          <div className="inline-block px-6 py-3 rounded-xl bg-gradient-to-r from-purple-600/30 to-blue-600/30 border border-purple-500/30">
            <div className="text-white font-bold text-lg">{rootDept.name}</div>
            <div className="text-gray-400 text-xs mt-1">{rootDept.description}</div>
          </div>
          <div className="h-8 w-px bg-surface-border mx-auto" />
          <div className="h-px bg-surface-border mx-auto" style={{ width: `${Math.min(childDepts.length * 25, 90)}%` }} />
        </div>
      )}

      {/* Child departments grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {childDepts.map((dept) => {
          const deptEmployees = getEmployees(dept.id);
          const head = deptEmployees.find((e) => e.is_department_head);
          const members = deptEmployees.filter((e) => !e.is_department_head);

          return (
            <div key={dept.id} className="bg-dark-light rounded-xl border border-surface-border overflow-hidden">
              {/* Department header */}
              <div className="px-4 py-3 bg-surface border-b border-surface-border">
                <h3 className="text-white font-semibold">{dept.name}</h3>
                <p className="text-gray-500 text-xs mt-0.5">{dept.description}</p>
              </div>

              {/* Department head */}
              {head && (
                <div className="px-4 py-3 border-b border-surface-border/50 bg-purple-600/5">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                      {head.name[0]}
                    </div>
                    <div>
                      <div className="text-white font-medium text-sm">
                        {head.name}
                        <span className="ml-1.5 px-1.5 py-0.5 rounded bg-purple-600/30 text-purple-300 text-xs">{head.position}</span>
                      </div>
                      <div className="text-gray-500 text-xs">{head.role}</div>
                    </div>
                  </div>
                  <div className="mt-1.5 text-xs text-gray-500 pl-12">
                    {head.email} · {head.phone}
                  </div>
                </div>
              )}

              {/* Team members */}
              <div className="divide-y divide-surface-border/30">
                {members.map((emp) => (
                  <div key={emp.id} className="px-4 py-2.5 hover:bg-white/5 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="w-7 h-7 rounded-full bg-surface-hover flex items-center justify-center text-gray-300 text-xs font-medium flex-shrink-0">
                        {emp.name[0]}
                      </div>
                      <div>
                        <div className="text-gray-200 text-sm">
                          {emp.name}
                          <span className="text-gray-500 text-xs ml-1.5">{emp.position}</span>
                        </div>
                        <div className="text-gray-500 text-xs">{emp.role}</div>
                      </div>
                    </div>
                    <div className="mt-1 text-xs text-gray-600 pl-10">
                      {emp.email} · {emp.phone}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
