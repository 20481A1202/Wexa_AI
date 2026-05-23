import { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { MailPlus } from "lucide-react";
import { api } from "../api/client";
import type { Role } from "../types/models";

export function TeamPage() {
  const queryClient = useQueryClient();
  const { data } = useQuery({ queryKey: ["organization"], queryFn: api.organization });
  const invite = useMutation({ mutationFn: api.invite });
  const updateMember = useMutation({
    mutationFn: ({ memberId, role }: { memberId: string; role: Role }) => api.updateMember(memberId, role),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["organization"] })
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    invite.mutate({ email: String(form.get("email")), role: String(form.get("role")) as Role });
    event.currentTarget.reset();
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
      <section className="rounded border border-slate-200 bg-white p-4">
        <h2 className="text-xl font-semibold text-ink">Team members</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[640px] border-collapse text-left text-sm">
            <thead>
              <tr className="border-b text-slate-500">
                <th className="py-3">Name</th>
                <th>Email</th>
                <th>Role</th>
              </tr>
            </thead>
            <tbody>
              {data?.members.map((member) => (
                <tr key={member.id} className="border-b last:border-0">
                  <td className="py-3 font-medium">{member.full_name}</td>
                  <td>{member.email}</td>
                  <td>
                    <select
                      className="focus-ring rounded border px-2 py-1"
                      value={member.role}
                      onChange={(event) => updateMember.mutate({ memberId: member.id, role: event.target.value as Role })}
                    >
                      <option>Owner</option>
                      <option>Admin</option>
                      <option>Analyst</option>
                      <option>Viewer</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <form onSubmit={submit} className="rounded border border-slate-200 bg-white p-4">
        <h2 className="font-semibold text-ink">Invite teammate</h2>
        <input name="email" required type="email" placeholder="Email" className="focus-ring mt-4 w-full rounded border px-3 py-2" />
        <select name="role" className="focus-ring mt-3 w-full rounded border px-3 py-2" defaultValue="Viewer">
          <option>Admin</option>
          <option>Analyst</option>
          <option>Viewer</option>
        </select>
        <button className="focus-ring mt-4 flex w-full items-center justify-center gap-2 rounded bg-mint px-3 py-2 text-white">
          <MailPlus size={16} />
          Send invite
        </button>
        {invite.isSuccess && (
          <div className="mt-4 space-y-2 rounded bg-slate-100 p-3 text-sm">
            <p className="font-medium text-mint">Invite email sent.</p>
            <a className="block break-all text-ocean" href={`/?invite_token=${invite.data.token}`}>
              Open invite link
            </a>
            <p className="break-all text-slate-600">Backup token: {invite.data.token}</p>
          </div>
        )}
        {invite.isError && <p className="mt-4 rounded bg-rose/10 p-3 text-sm text-rose">{(invite.error as Error).message}</p>}
      </form>
    </div>
  );
}
