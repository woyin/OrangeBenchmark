import { render, screen, fireEvent } from '@testing-library/react'
import DataTable from './DataTable'

const columns = [
  { key: 'name', label: 'Name', sortable: true },
  { key: 'age', label: 'Age', sortable: true },
]
const data = [
  { name: 'Alice', age: 30 },
  { name: 'Bob', age: 25 },
  { name: 'Charlie', age: 35 },
]

describe('DataTable', () => {
  test('renders table headers', () => {
    render(<DataTable columns={columns} data={data} />)
    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Age')).toBeInTheDocument()
  })

  test('renders data rows', () => {
    render(<DataTable columns={columns} data={data} />)
    expect(screen.getByText('Alice')).toBeInTheDocument()
    expect(screen.getByText('Bob')).toBeInTheDocument()
  })

  test('sorts by column', () => {
    render(<DataTable columns={columns} data={data} />)
    fireEvent.click(screen.getByText('Name'))
    const rows = screen.getAllByRole('row')
    expect(rows[1]).toHaveTextContent('Alice')
  })

  test('filters rows', () => {
    render(<DataTable columns={columns} data={data} />)
    const input = screen.getByPlaceholderText(/search|filter/i)
    fireEvent.change(input, { target: { value: 'Alice' } })
    expect(screen.getByText('Alice')).toBeInTheDocument()
    expect(screen.queryByText('Bob')).not.toBeInTheDocument()
  })

  test('pagination info', () => {
    render(<DataTable columns={columns} data={data} pageSize={2} />)
    expect(screen.getByText(/page/i)).toBeInTheDocument()
  })
})
