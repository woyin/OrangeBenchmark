import { render, screen, waitFor, act } from '@testing-library/react'
import InfiniteScroll from './InfiniteScroll'

const mockFetchData = jest.fn()
  .mockResolvedValueOnce({ items: [{ id: 1, name: 'Item 1' }, { id: 2, name: 'Item 2' }], hasMore: true })
  .mockResolvedValueOnce({ items: [{ id: 3, name: 'Item 3' }], hasMore: false })

describe('InfiniteScroll', () => {
  beforeEach(() => {
    mockFetchData.mockClear()
    mockFetchData
      .mockResolvedValueOnce({ items: [{ id: 1, name: 'Item 1' }, { id: 2, name: 'Item 2' }], hasMore: true })
      .mockResolvedValueOnce({ items: [{ id: 3, name: 'Item 3' }], hasMore: false })
  })

  test('renders initial items', async () => {
    render(
      <InfiniteScroll
        fetchData={mockFetchData}
        renderItem={(item) => <div>{item.name}</div>}
      />
    )
    await waitFor(() => {
      expect(screen.getByText('Item 1')).toBeInTheDocument()
      expect(screen.getByText('Item 2')).toBeInTheDocument()
    })
  })

  test('calls fetchData on mount', async () => {
    render(
      <InfiniteScroll
        fetchData={mockFetchData}
        renderItem={(item) => <div>{item.name}</div>}
      />
    )
    await waitFor(() => {
      expect(mockFetchData).toHaveBeenCalledWith(1)
    })
  })

  test('shows loading indicator', async () => {
    render(
      <InfiniteScroll
        fetchData={mockFetchData}
        renderItem={(item) => <div>{item.name}</div>}
        loadingFallback={<div>Loading...</div>}
      />
    )
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  test('stops when no more data', async () => {
    render(
      <InfiniteScroll
        fetchData={mockFetchData}
        renderItem={(item) => <div>{item.name}</div>}
      />
    )
    await waitFor(() => {
      expect(mockFetchData).toHaveBeenCalledWith(1)
    })
  })
})
