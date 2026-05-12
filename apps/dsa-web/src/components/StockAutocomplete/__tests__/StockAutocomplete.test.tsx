/**
 * StockAutocomplete component tests.
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { StockAutocomplete } from '../StockAutocomplete';
import type { StockIndexItem } from '../../../types/stockIndex';

let stockIndexHookImpl: () => {
  index: StockIndexItem[];
  loading: boolean;
  fallback: boolean;
  error: Error | null;
  loaded: boolean;
};

let autocompleteHookImpl: () => {
  query: string;
  setQuery: ReturnType<typeof vi.fn>;
  suggestions: typeof mockSuggestions;
  isOpen: boolean;
  highlightedIndex: number;
  setHighlightedIndex: ReturnType<typeof vi.fn>;
  highlightPrevious: ReturnType<typeof vi.fn>;
  highlightNext: ReturnType<typeof vi.fn>;
  handleSelect: ReturnType<typeof vi.fn>;
  close: ReturnType<typeof vi.fn>;
  reset: ReturnType<typeof vi.fn>;
  isComposing: boolean;
  setIsComposing: ReturnType<typeof vi.fn>;
  runtimeFallback: boolean;
  error: Error | null;
};

// Mock the hooks
vi.mock('../../../hooks/useStockIndex', () => ({
  useStockIndex: () => stockIndexHookImpl(),
}));

vi.mock('../../../hooks/useAutocomplete', () => ({
  useAutocomplete: () => autocompleteHookImpl(),
}));

const mockIndex: StockIndexItem[] = [
  {
    canonicalCode: "2330.TW",
    displayCode: "2330",
    nameZh: "台積電",
    pinyinFull: "taijidian",
    pinyinAbbr: "tjd",
    aliases: ["台積電"],
    market: "TW",
    assetType: "stock",
    active: true,
    popularity: 100,
  },
];

const mockSuggestions = [
  {
    canonicalCode: "2330.TW",
    displayCode: "2330",
    nameZh: "台積電",
    market: "TW",
    matchType: "exact" as const,
    matchField: "code" as const,
    score: 100,
  },
];

const twSuggestion = {
  canonicalCode: "2330.TW",
  displayCode: "2330",
  nameZh: "台積電",
  market: "TW" as const,
  matchType: "exact" as const,
  matchField: "code" as const,
  score: 100,
};

const usSuggestion = {
  canonicalCode: "AAPL",
  displayCode: "AAPL",
  nameZh: "蘋果",
  market: "US" as const,
  matchType: "exact" as const,
  matchField: "code" as const,
  score: 100,
};

describe('StockAutocomplete', () => {
  const mockOnChange = vi.fn();
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    stockIndexHookImpl = () => ({
      index: mockIndex,
      loading: false,
      fallback: false,
      error: null,
      loaded: true,
    });
    autocompleteHookImpl = () => ({
      query: '',
      setQuery: vi.fn(),
      suggestions: mockSuggestions,
      isOpen: false,
      highlightedIndex: -1,
      setHighlightedIndex: vi.fn(),
      highlightPrevious: vi.fn(),
      highlightNext: vi.fn(),
      handleSelect: vi.fn(),
      close: vi.fn(),
      reset: vi.fn(),
      isComposing: false,
      setIsComposing: vi.fn(),
      runtimeFallback: false,
      error: null,
    });
  });

  it('renders the input element', () => {
    render(
      <StockAutocomplete
        value=""
        onChange={mockOnChange}
        onSubmit={mockOnSubmit}
      />
    );

    const input = screen.getByPlaceholderText(/輸入股票程式碼或名稱/);
    expect(input).toBeInTheDocument();
  });

  it('renders a custom placeholder', () => {
    render(
      <StockAutocomplete
        value=""
        onChange={mockOnChange}
        onSubmit={mockOnSubmit}
        placeholder="請輸入程式碼"
      />
    );

    const input = screen.getByPlaceholderText(/請輸入程式碼/);
    expect(input).toBeInTheDocument();
  });

  it('renders the current value', () => {
    render(
      <StockAutocomplete
        value="2330"
        onChange={mockOnChange}
        onSubmit={mockOnSubmit}
      />
    );

    const input = screen.getByDisplayValue('2330');
    expect(input).toBeInTheDocument();
  });

  it('supports the disabled state', () => {
    render(
      <StockAutocomplete
        value=""
        onChange={mockOnChange}
        onSubmit={mockOnSubmit}
        disabled={true}
      />
    );

    const input = screen.getByRole('combobox');
    expect(input).toBeDisabled();
  });

  it('calls onChange when the input changes', () => {
    render(
      <StockAutocomplete
        value=""
        onChange={mockOnChange}
        onSubmit={mockOnSubmit}
      />
    );

    const input = screen.getByRole('combobox');
    fireEvent.change(input, { target: { value: '2330' } });

    expect(mockOnChange).toHaveBeenCalledWith('2330');
  });

  it('applies a custom class name', () => {
    const { container } = render(
      <StockAutocomplete
        value=""
        onChange={mockOnChange}
        onSubmit={mockOnSubmit}
        className="custom-class"
      />
    );

    const input = container.querySelector('.custom-class');
    expect(input).toBeInTheDocument();
  });

  it('exposes the expected accessibility attributes', () => {
    render(
      <StockAutocomplete
        value=""
        onChange={mockOnChange}
        onSubmit={mockOnSubmit}
      />
    );

    const input = screen.getByRole('combobox');
    expect(input).toHaveAttribute('aria-autocomplete', 'none');
    expect(input).toHaveAttribute('role', 'combobox');
  });

  describe('fallback mode', () => {
    it('renders a plain input when index loading fallback is active', () => {
      stockIndexHookImpl = () => ({
        index: [],
        loading: false,
        fallback: true,
        error: new Error('Index load failed'),
        loaded: false,
      });

      render(
        <StockAutocomplete
          value=""
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const input = screen.getByPlaceholderText(/輸入股票程式碼或名稱/);
      expect(input).toHaveAttribute('data-autocomplete-mode', 'fallback');
    });

    it('renders a plain input when autocomplete runtime fallback is active', () => {
      autocompleteHookImpl = () => ({
        query: '',
        setQuery: vi.fn(),
        suggestions: [],
        isOpen: false,
        highlightedIndex: -1,
        setHighlightedIndex: vi.fn(),
        highlightPrevious: vi.fn(),
        highlightNext: vi.fn(),
        handleSelect: vi.fn(),
        close: vi.fn(),
        reset: vi.fn(),
        isComposing: false,
        setIsComposing: vi.fn(),
        runtimeFallback: true,
        error: new Error('Search crashed'),
      });

      render(
        <StockAutocomplete
          value=""
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const input = screen.getByPlaceholderText(/輸入股票程式碼或名稱/);
      expect(input).toHaveAttribute('data-autocomplete-mode', 'fallback');
    });

    it('submits manually when fallback input receives Enter', () => {
      autocompleteHookImpl = () => ({
        query: '',
        setQuery: vi.fn(),
        suggestions: [],
        isOpen: false,
        highlightedIndex: -1,
        setHighlightedIndex: vi.fn(),
        highlightPrevious: vi.fn(),
        highlightNext: vi.fn(),
        handleSelect: vi.fn(),
        close: vi.fn(),
        reset: vi.fn(),
        isComposing: false,
        setIsComposing: vi.fn(),
        runtimeFallback: true,
        error: new Error('Search crashed'),
      });

      render(
        <StockAutocomplete
          value="2330"
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const input = screen.getByDisplayValue('2330');
      fireEvent.keyDown(input, { key: 'Enter' });

      expect(mockOnSubmit).toHaveBeenCalledWith('2330');
    });
  });

  describe('IME support', () => {
    it('handles composition start and end events', () => {
      render(
        <StockAutocomplete
          value=""
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const input = screen.getByRole('combobox');

      fireEvent.compositionStart(input);
      fireEvent.compositionEnd(input);

      // The events should be handled without throwing.
      expect(input).toBeInTheDocument();
    });
  });

  describe('keyboard submission', () => {
    it('submits the raw input when suggestions are open but nothing is highlighted', () => {
      autocompleteHookImpl = () => ({
        query: '',
        setQuery: vi.fn(),
        suggestions: mockSuggestions,
        isOpen: true,
        highlightedIndex: -1,
        setHighlightedIndex: vi.fn(),
        highlightPrevious: vi.fn(),
        highlightNext: vi.fn(),
        handleSelect: vi.fn(),
        close: vi.fn(),
        reset: vi.fn(),
        isComposing: false,
        setIsComposing: vi.fn(),
        runtimeFallback: false,
        error: null,
      });

      render(
        <StockAutocomplete
          value="233"
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const input = screen.getByDisplayValue('233');
      fireEvent.keyDown(input, { key: 'Enter' });

      expect(mockOnSubmit).toHaveBeenCalledWith('233');
    });

    it('submits the highlighted suggestion when one is explicitly selected', () => {
      autocompleteHookImpl = () => ({
        query: '',
        setQuery: vi.fn(),
        suggestions: mockSuggestions,
        isOpen: true,
        highlightedIndex: 0,
        setHighlightedIndex: vi.fn(),
        highlightPrevious: vi.fn(),
        highlightNext: vi.fn(),
        handleSelect: vi.fn(),
        close: vi.fn(),
        reset: vi.fn(),
        isComposing: false,
        setIsComposing: vi.fn(),
        runtimeFallback: false,
        error: null,
      });

      render(
        <StockAutocomplete
          value="233"
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const input = screen.getByDisplayValue('233');
      fireEvent.keyDown(input, { key: 'Enter' });

      expect(mockOnChange).toHaveBeenCalledWith('2330');
      expect(mockOnSubmit).toHaveBeenCalledWith('2330.TW', '台積電', 'autocomplete');
    });

    it('submits the highlighted TW suggestion using the canonical .TW code', () => {
      autocompleteHookImpl = () => ({
        query: '',
        setQuery: vi.fn(),
        suggestions: [twSuggestion],
        isOpen: true,
        highlightedIndex: 0,
        setHighlightedIndex: vi.fn(),
        highlightPrevious: vi.fn(),
        highlightNext: vi.fn(),
        handleSelect: vi.fn(),
        close: vi.fn(),
        reset: vi.fn(),
        isComposing: false,
        setIsComposing: vi.fn(),
        runtimeFallback: false,
        error: null,
      });

      render(
        <StockAutocomplete
          value="2330"
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const input = screen.getByDisplayValue('2330');
      fireEvent.keyDown(input, { key: 'Enter' });

      expect(mockOnChange).toHaveBeenCalledWith('2330');
      expect(mockOnSubmit).toHaveBeenCalledWith('2330.TW', '台積電', 'autocomplete');
    });

    it('submits the highlighted US suggestion using the ticker symbol', () => {
      autocompleteHookImpl = () => ({
        query: '',
        setQuery: vi.fn(),
        suggestions: [usSuggestion],
        isOpen: true,
        highlightedIndex: 0,
        setHighlightedIndex: vi.fn(),
        highlightPrevious: vi.fn(),
        highlightNext: vi.fn(),
        handleSelect: vi.fn(),
        close: vi.fn(),
        reset: vi.fn(),
        isComposing: false,
        setIsComposing: vi.fn(),
        runtimeFallback: false,
        error: null,
      });

      render(
        <StockAutocomplete
          value="AAPL"
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const input = screen.getByDisplayValue('AAPL');
      fireEvent.keyDown(input, { key: 'Enter' });

      expect(mockOnChange).toHaveBeenCalledWith('AAPL');
      expect(mockOnSubmit).toHaveBeenCalledWith('AAPL', '蘋果', 'autocomplete');
    });
  });

  describe('runtime boundary', () => {
    it('falls back to the plain input when the autocomplete tree throws during render', () => {
      autocompleteHookImpl = () => {
        throw new Error('Autocomplete render failed');
      };

      render(
        <StockAutocomplete
          value="META"
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const input = screen.getByDisplayValue('META');
      expect(input).toHaveAttribute('data-autocomplete-mode', 'fallback');
    });

    it('falls back to the plain input when a suggestion contains an unsupported market', () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      autocompleteHookImpl = () => ({
        query: '',
        setQuery: vi.fn(),
        suggestions: [
          {
            canonicalCode: 'TEST.OTC',
            displayCode: 'TEST',
            nameZh: '測試市場',
            market: 'OTC' as never,
            matchType: 'exact' as const,
            matchField: 'code' as const,
            score: 100,
          },
        ],
        isOpen: true,
        highlightedIndex: 0,
        setHighlightedIndex: vi.fn(),
        highlightPrevious: vi.fn(),
        highlightNext: vi.fn(),
        handleSelect: vi.fn(),
        close: vi.fn(),
        reset: vi.fn(),
        isComposing: false,
        setIsComposing: vi.fn(),
        runtimeFallback: false,
        error: null,
      });

      render(
        <StockAutocomplete
          value="TEST"
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const input = screen.getByDisplayValue('TEST');
      fireEvent.focus(input);

      const fallbackInput = screen.getByDisplayValue('TEST');
      expect(fallbackInput).toHaveAttribute('data-autocomplete-mode', 'fallback');
      expect(consoleErrorSpy).toHaveBeenCalled();
      consoleErrorSpy.mockRestore();
    });
  });
});
