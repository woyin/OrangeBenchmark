interface DataTableProps {
  columns: { key: string; label: string; sortable?: boolean }[]
  data: Record<string, any>[]
  pageSize?: number
}
export default function DataTable({ columns, data, pageSize = 10 }: DataTableProps) {
  return <table><tbody></tbody></table>
}
