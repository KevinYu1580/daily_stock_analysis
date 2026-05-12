/**
 * Stock Index Type Definitions
 *
 * Stock data index for autocomplete functionality
 */

export type Market = 'TW' | 'US' | 'INDEX' | 'ETF';
export type AssetType = 'stock' | 'index' | 'etf';

/**
 * Stock index item (full format)
 */
export interface StockIndexItem {
  /** Canonical code: 2330.TW */
  canonicalCode: string;
  /** Display code: 2330 */
  displayCode: string;
  /** Chinese name: 台積電 */
  nameZh: string;
  /** English name: TSMC */
  nameEn?: string;
  /** Pinyin full: taijidian */
  pinyinFull?: string;
  /** Pinyin abbreviation: tjd */
  pinyinAbbr?: string;
  /** Aliases: ["台積電"] */
  aliases?: string[];
  /** Market */
  market: Market;
  /** Asset type */
  assetType: AssetType;
  /** Is active */
  active: boolean;
  /** Popularity */
  popularity?: number;
}

/**
 * Stock search suggestion item
 */
export interface StockSuggestion {
  /** Canonical code */
  canonicalCode: string;
  /** Display code */
  displayCode: string;
  /** Chinese name */
  nameZh: string;
  /** Market */
  market: Market;
  /** Match type */
  matchType: 'exact' | 'prefix' | 'contains' | 'fuzzy';
  /** Match field */
  matchField: 'code' | 'name' | 'pinyin' | 'alias';
  /** Sort score */
  score: number;
}

/**
 * Compressed format stock index item (for reducing file size)
 */
export type StockIndexTuple = [
  string,  // canonicalCode
  string,  // displayCode
  string,  // nameZh
  string | undefined, // pinyinFull
  string | undefined, // pinyinAbbr
  string[], // aliases (required, use empty array if none)
  Market,
  AssetType,
  boolean, // active
  number | undefined, // popularity
];

/**
 * Stock index data (supports two formats)
 */
export type StockIndexData = StockIndexItem[] | StockIndexTuple[];
