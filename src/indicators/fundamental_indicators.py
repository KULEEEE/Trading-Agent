"""Fundamental analysis indicators using Yahoo Finance data."""

import math
from typing import Dict, Optional, List
from ..api import YahooFinanceClient
from ..utils import log


def _safe(val, default=0):
    """Return default if value is None or NaN."""
    if val is None:
        return default
    try:
        if isinstance(val, float) and math.isnan(val):
            return default
    except TypeError:
        return default
    return val


class FundamentalIndicators:
    """Calculate and interpret fundamental analysis indicators."""

    def __init__(self):
        self.client = YahooFinanceClient()

    def get_fundamentals(self, symbol: str) -> Dict:
        """
        Get all fundamental indicators for a symbol.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with categorized fundamental data
        """
        info = self.client.get_stock_info(symbol)

        if not info:
            log.warning(f"No fundamental data for {symbol}")
            return {}

        fundamentals = {
            'symbol': symbol,
            'name': info.get('longName', symbol),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'current_price': _safe(info.get('currentPrice')),
            'market_cap': _safe(info.get('marketCap')),

            # Valuation
            'valuation': {
                'trailing_pe': _safe(info.get('trailingPE')),
                'forward_pe': _safe(info.get('forwardPE')),
                'peg_ratio': _safe(info.get('trailingPegRatio')),
                'price_to_book': _safe(info.get('priceToBook')),
                'price_to_sales': _safe(info.get('priceToSalesTrailing12Months')),
                'ev_to_revenue': _safe(info.get('enterpriseToRevenue')),
                'ev_to_ebitda': _safe(info.get('enterpriseToEbitda')),
                'enterprise_value': _safe(info.get('enterpriseValue')),
                'book_value': _safe(info.get('bookValue')),
            },

            # Profitability
            'profitability': {
                'gross_margins': _safe(info.get('grossMargins')),
                'operating_margins': _safe(info.get('operatingMargins')),
                'profit_margins': _safe(info.get('profitMargins')),
                'ebitda_margins': _safe(info.get('ebitdaMargins')),
                'return_on_assets': _safe(info.get('returnOnAssets')),
                'return_on_equity': _safe(info.get('returnOnEquity')),
            },

            # Growth
            'growth': {
                'earnings_growth': _safe(info.get('earningsGrowth')),
                'quarterly_earnings_growth': _safe(info.get('earningsQuarterlyGrowth')),
                'revenue_growth': _safe(info.get('revenueGrowth')),
            },

            # Financial Health
            'financial_health': {
                'current_ratio': _safe(info.get('currentRatio')),
                'quick_ratio': _safe(info.get('quickRatio')),
                'debt_to_equity': _safe(info.get('debtToEquity')),
                'total_cash': _safe(info.get('totalCash')),
                'total_debt': _safe(info.get('totalDebt')),
                'free_cashflow': _safe(info.get('freeCashflow')),
                'operating_cashflow': _safe(info.get('operatingCashflow')),
                'total_revenue': _safe(info.get('totalRevenue')),
                'ebitda': _safe(info.get('ebitda')),
                'net_income': _safe(info.get('netIncomeToCommon')),
            },

            # EPS
            'eps': {
                'trailing_eps': _safe(info.get('epsTrailingTwelveMonths')),
                'forward_eps': _safe(info.get('epsForward')),
                'current_year_eps': _safe(info.get('epsCurrentYear')),
                'revenue_per_share': _safe(info.get('revenuePerShare')),
            },

            # Dividends
            # Note: yfinance returns dividendYield and fiveYearAvgDividendYield
            # already as percentages (0.38 = 0.38%), so we convert to decimal
            # form (0.0038) for consistency with other ratio fields.
            'dividends': {
                'dividend_rate': _safe(info.get('dividendRate')),
                'dividend_yield': _safe(info.get('dividendYield')) / 100,
                'payout_ratio': _safe(info.get('payoutRatio')),
                'five_year_avg_yield': _safe(info.get('fiveYearAvgDividendYield')),
                'ex_dividend_date': info.get('exDividendDate'),
            },

            # Risk & Beta
            'risk': {
                'beta': _safe(info.get('beta')),
                'audit_risk': _safe(info.get('auditRisk')),
                'board_risk': _safe(info.get('boardRisk')),
                'compensation_risk': _safe(info.get('compensationRisk')),
                'overall_risk': _safe(info.get('overallRisk')),
                '52_week_high': _safe(info.get('fiftyTwoWeekHigh')),
                '52_week_low': _safe(info.get('fiftyTwoWeekLow')),
                '52_week_change': _safe(info.get('52WeekChange')),
            },

            # Analyst
            'analyst': {
                'target_high': _safe(info.get('targetHighPrice')),
                'target_low': _safe(info.get('targetLowPrice')),
                'target_mean': _safe(info.get('targetMeanPrice')),
                'target_median': _safe(info.get('targetMedianPrice')),
                'recommendation': info.get('recommendationKey', 'N/A'),
                'num_analysts': _safe(info.get('numberOfAnalystOpinions')),
            },

            # Ownership
            'ownership': {
                'insider_pct': _safe(info.get('heldPercentInsiders')),
                'institution_pct': _safe(info.get('heldPercentInstitutions')),
                'short_ratio': _safe(info.get('shortRatio')),
                'short_pct_float': _safe(info.get('shortPercentOfFloat')),
            },
        }

        log.info(f"Fetched fundamentals for {symbol}")
        return fundamentals

    def interpret_valuation(self, fundamentals: Dict) -> Dict:
        """
        Interpret valuation metrics and provide ratings.

        Args:
            fundamentals: Fundamental data dictionary

        Returns:
            Dictionary with interpretations
        """
        val = fundamentals.get('valuation', {})
        interpretations = {}

        # P/E Ratio interpretation
        pe = val.get('trailing_pe', 0)
        if pe > 0:
            if pe < 15:
                interpretations['pe_rating'] = 'Undervalued'
                interpretations['pe_score'] = 5
            elif pe < 20:
                interpretations['pe_rating'] = 'Fair'
                interpretations['pe_score'] = 4
            elif pe < 25:
                interpretations['pe_rating'] = 'Slightly Overvalued'
                interpretations['pe_score'] = 3
            elif pe < 35:
                interpretations['pe_rating'] = 'Overvalued'
                interpretations['pe_score'] = 2
            else:
                interpretations['pe_rating'] = 'Very Overvalued'
                interpretations['pe_score'] = 1
        else:
            interpretations['pe_rating'] = 'Negative Earnings'
            interpretations['pe_score'] = 0

        # P/B Ratio interpretation
        pb = val.get('price_to_book', 0)
        if pb > 0:
            if pb < 1:
                interpretations['pb_rating'] = 'Undervalued'
                interpretations['pb_score'] = 5
            elif pb < 3:
                interpretations['pb_rating'] = 'Fair'
                interpretations['pb_score'] = 4
            elif pb < 5:
                interpretations['pb_rating'] = 'Growth Premium'
                interpretations['pb_score'] = 3
            else:
                interpretations['pb_rating'] = 'High Premium'
                interpretations['pb_score'] = 2

        # PEG Ratio interpretation
        peg = val.get('peg_ratio', 0)
        if peg > 0:
            if peg < 1:
                interpretations['peg_rating'] = 'Undervalued (growth)'
                interpretations['peg_score'] = 5
            elif peg < 1.5:
                interpretations['peg_rating'] = 'Fair (growth-adjusted)'
                interpretations['peg_score'] = 4
            elif peg < 2:
                interpretations['peg_rating'] = 'Slightly Overvalued'
                interpretations['peg_score'] = 3
            else:
                interpretations['peg_rating'] = 'Overvalued (growth-adjusted)'
                interpretations['peg_score'] = 2

        # EV/EBITDA interpretation
        ev_ebitda = val.get('ev_to_ebitda', 0)
        if ev_ebitda > 0:
            if ev_ebitda < 10:
                interpretations['ev_ebitda_rating'] = 'Cheap'
                interpretations['ev_ebitda_score'] = 5
            elif ev_ebitda < 15:
                interpretations['ev_ebitda_rating'] = 'Fair'
                interpretations['ev_ebitda_score'] = 4
            elif ev_ebitda < 20:
                interpretations['ev_ebitda_rating'] = 'Pricey'
                interpretations['ev_ebitda_score'] = 3
            else:
                interpretations['ev_ebitda_rating'] = 'Expensive'
                interpretations['ev_ebitda_score'] = 2

        # Overall valuation score (average of available scores)
        scores = [v for k, v in interpretations.items() if k.endswith('_score') and v > 0]
        interpretations['overall_score'] = sum(scores) / len(scores) if scores else 0

        if interpretations['overall_score'] >= 4:
            interpretations['overall_rating'] = 'Undervalued'
        elif interpretations['overall_score'] >= 3:
            interpretations['overall_rating'] = 'Fair Value'
        elif interpretations['overall_score'] >= 2:
            interpretations['overall_rating'] = 'Overvalued'
        else:
            interpretations['overall_rating'] = 'Very Overvalued'

        return interpretations

    def interpret_profitability(self, fundamentals: Dict) -> Dict:
        """
        Interpret profitability metrics.

        Args:
            fundamentals: Fundamental data dictionary

        Returns:
            Dictionary with profitability interpretations
        """
        prof = fundamentals.get('profitability', {})
        interpretations = {}

        # ROE interpretation
        roe = prof.get('return_on_equity', 0)
        if roe > 0.20:
            interpretations['roe_rating'] = 'Excellent'
        elif roe > 0.15:
            interpretations['roe_rating'] = 'Good'
        elif roe > 0.10:
            interpretations['roe_rating'] = 'Average'
        elif roe > 0:
            interpretations['roe_rating'] = 'Below Average'
        else:
            interpretations['roe_rating'] = 'Negative'

        # ROA interpretation
        roa = prof.get('return_on_assets', 0)
        if roa > 0.10:
            interpretations['roa_rating'] = 'Excellent'
        elif roa > 0.05:
            interpretations['roa_rating'] = 'Good'
        elif roa > 0:
            interpretations['roa_rating'] = 'Average'
        else:
            interpretations['roa_rating'] = 'Negative'

        # Profit margin interpretation
        margin = prof.get('profit_margins', 0)
        if margin > 0.20:
            interpretations['margin_rating'] = 'Excellent'
        elif margin > 0.10:
            interpretations['margin_rating'] = 'Good'
        elif margin > 0.05:
            interpretations['margin_rating'] = 'Average'
        elif margin > 0:
            interpretations['margin_rating'] = 'Low'
        else:
            interpretations['margin_rating'] = 'Loss-making'

        return interpretations

    def interpret_financial_health(self, fundamentals: Dict) -> Dict:
        """
        Interpret financial health metrics.

        Args:
            fundamentals: Fundamental data dictionary

        Returns:
            Dictionary with financial health interpretations
        """
        health = fundamentals.get('financial_health', {})
        interpretations = {}

        # Current Ratio interpretation
        cr = health.get('current_ratio', 0)
        if cr > 2:
            interpretations['current_ratio_rating'] = 'Strong'
        elif cr > 1.5:
            interpretations['current_ratio_rating'] = 'Healthy'
        elif cr > 1:
            interpretations['current_ratio_rating'] = 'Adequate'
        else:
            interpretations['current_ratio_rating'] = 'Weak'

        # Debt to Equity interpretation
        de = health.get('debt_to_equity', 0)
        if de < 30:
            interpretations['debt_rating'] = 'Low Leverage'
        elif de < 60:
            interpretations['debt_rating'] = 'Moderate Leverage'
        elif de < 100:
            interpretations['debt_rating'] = 'High Leverage'
        else:
            interpretations['debt_rating'] = 'Very High Leverage'

        # Free Cash Flow
        fcf = health.get('free_cashflow', 0)
        if fcf > 0:
            interpretations['fcf_rating'] = 'Positive FCF'
        else:
            interpretations['fcf_rating'] = 'Negative FCF (Caution)'

        return interpretations

    def get_full_analysis(self, symbol: str) -> Dict:
        """
        Get complete fundamental analysis with interpretations.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with full analysis
        """
        fundamentals = self.get_fundamentals(symbol)

        if not fundamentals:
            return {}

        analysis = {
            **fundamentals,
            'valuation_interpretation': self.interpret_valuation(fundamentals),
            'profitability_interpretation': self.interpret_profitability(fundamentals),
            'health_interpretation': self.interpret_financial_health(fundamentals),
        }

        log.info(f"Full fundamental analysis complete for {symbol}")
        return analysis

    def compare_symbols(self, symbols: List[str]) -> Dict:
        """
        Compare fundamental metrics across multiple symbols.

        Args:
            symbols: List of stock ticker symbols

        Returns:
            Dictionary with comparison data
        """
        comparisons = {}

        for symbol in symbols:
            analysis = self.get_full_analysis(symbol)
            if analysis:
                comparisons[symbol] = analysis

        log.info(f"Compared fundamentals for {len(comparisons)} symbols")
        return comparisons

    def format_number(self, num, prefix='', suffix='', decimals=2):
        """Format large numbers with K/M/B suffixes."""
        if num is None or num == 0:
            return f"{prefix}0{suffix}"

        abs_num = abs(num)
        sign = '-' if num < 0 else ''

        if abs_num >= 1e12:
            return f"{sign}{prefix}{abs_num/1e12:.{decimals}f}T{suffix}"
        elif abs_num >= 1e9:
            return f"{sign}{prefix}{abs_num/1e9:.{decimals}f}B{suffix}"
        elif abs_num >= 1e6:
            return f"{sign}{prefix}{abs_num/1e6:.{decimals}f}M{suffix}"
        elif abs_num >= 1e3:
            return f"{sign}{prefix}{abs_num/1e3:.{decimals}f}K{suffix}"
        else:
            return f"{sign}{prefix}{abs_num:.{decimals}f}{suffix}"
