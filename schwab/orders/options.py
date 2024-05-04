import datetime

from schwab.orders.generic import OrderBuilder


def _parse_expiration_date(expiration_date):
    try:
        date = datetime.datetime.strptime(expiration_date, '%y%m%d')
        return datetime.date(year=date.year, month=date.month, day=date.day)
    except ValueError:
        pass

    raise ValueError(
        'expiration date must follow format ' +
        '[Two digit year][Two digit month]' +
        '[Two digit day]')


class OptionSymbol:
    '''Construct an option symbol from its constituent parts. Options symbols
    have the following format: ``[Underlying][2 spaces][Two digit year]
    [Two digit month][Two digit day]['P' or 'C'][Strike price]``

    The format of the strike price is modified based on its amount:
     * If less than 1000, Strike Price is multiplied by 1000 and pre-pended with
       two zeroes
     * If >= 1000, it's multiplied by 1000 and prepended with one zero.

     Examples include:
     * ``QQQ  240420P00500000``: QQQ Apr 20, 2024 500 Put (note the two zeroes
       in front because strike is less than 1000)
     * ``SPXW  240420C05040000``: SPX Weekly Apr 20, 2024 5040 Call (note the
       one zero in front because strike is greater than 1000)
     
    Note while each of the individual parts is validated by itself, the
    option symbol itself may not represent a traded option:

     * Some underlyings do not support options.
     * Not all dates have valid option expiration dates.
     * Not all strike prices are valid options strikes.

    You can use :meth:`~schwab.client.Client.get_option_chain` to obtain real
    option symbols for an underlying, as well as extensive data in pricing,
    bid/ask spread, volume, etc.

    :param underlying_symbol: Symbol of the underlying. Not validated.
    :param expiration_date: Expiration date. Accepts ``datetime.date``,
                            ``datetime.datetime``, or strings with the
                            format ``[Two digit year][Two digit month][Two
                            digit day]``.
    :param contract_type: ``P` or `PUT`` for put and ``C` or `CALL`` for call.
    :param strike_price_as_string: Strike price, represented by a string as
                                   you would see at the end of a real option
                                   symbol.

    '''

    def __init__(self, underlying_symbol, expiration_date, contract_type,
                 strike_price_as_string):
        self.underlying_symbol = underlying_symbol

        if contract_type in ('C', 'CALL'):
            self.contract_type = 'C'
        elif contract_type in ('P', 'PUT'):
            self.contract_type = 'P'
        else:
            raise ValueError(
                'Contract type must be one of \'C\', \'CALL\', \'P\' or \'PUT\'')

        if isinstance(expiration_date, str):
            self.expiration_date = _parse_expiration_date(expiration_date)
        elif isinstance(expiration_date, datetime.datetime):
            self.expiration_date = datetime.date(
                year=expiration_date.year,
                month=expiration_date.month,
                day=expiration_date.day)
        elif isinstance(expiration_date, datetime.date):
            self.expiration_date = expiration_date
        else:
            raise ValueError(
                'expiration_date must be a string with format %y%m%d ' +
                '(e.g. 240119) or one of datetime.date or ' +
                'datetime.datetime')

        assert (isinstance(self.expiration_date, datetime.date))

        try:
            strike = float(strike_price_as_string)
            if strike <= 0:
                raise ValueError('Strike price must be a positive number.')
        except ValueError:
            raise ValueError('Strike price must be a string representing a positive float')
        # Prepend zeroes based on strike price
        if strike < 1000:
            strike_price_as_string = '00' + str(int(strike * 1000))
        else:
            strike_price_as_string = '0' + str(int(strike * 1000))
        self.strike_price = strike_price_as_string

    @classmethod
    def parse_symbol(cls, symbol):
        '''
        Parse a string option symbol of the for ``[Underlying]_[Two digit month]
        [Two digit day][Two digit year]['P' or 'C'][Strike price]``.
        '''
        format_error_str = (
            'option symbol must have format ' +
            '[Underlying]_[Expiration][P/C][Strike]')

        # Underlying
        try:
            underlying, rest = symbol.split('_')
        except ValueError:
            underlying, rest = None, None
        if underlying is None:
            raise ValueError('option symbol missing underscore \'_\', ' +
                             format_error_str)

        # Expiration
        type_split = rest.split('P')
        if len(type_split) == 2:
            expiration_date, strike = type_split
            contract_type = 'P'
        else:
            type_split = rest.split('C')
            if len(type_split) == 2:
                expiration_date, strike = type_split
                contract_type = 'C'
            else:
                raise ValueError(
                    r'option must have contract type \'C\' r \'\P\', ' +
                    format_error_str)

        expiration_date = _parse_expiration_date(expiration_date)

        return OptionSymbol(underlying, expiration_date, contract_type, strike)

    def build(self):
        '''
        Returns the option symbol represented by this builder.
        '''
        return '{}  {}{}{}'.format(
            self.underlying_symbol,
            self.expiration_date.strftime('%y%m%d'),
            self.contract_type,
            self.strike_price
        )


def __base_builder():
    from schwab.orders.common import Duration, Session

    return (OrderBuilder()
            .set_session(Session.NORMAL)
            .set_duration(Duration.DAY))


################################################################################
# Single options

# Buy to Open

def option_buy_to_open_market(symbol, quantity):
    '''
    Returns a pre-filled :class:`~schwab.orders.generic.OrderBuilder` for a
    buy-to-open market order.
    '''
    from schwab.orders.common import OptionInstruction, OrderType, OrderStrategyType

    return (__base_builder()
            .set_order_type(OrderType.MARKET)
            .set_order_strategy_type(OrderStrategyType.SINGLE)
            .add_option_leg(OptionInstruction.BUY_TO_OPEN, symbol, quantity))


def option_buy_to_open_limit(symbol, quantity, price):
    '''
    Returns a pre-filled :class:`~schwab.orders.generic.OrderBuilder` for a
    buy-to-open limit order.
    '''
    from schwab.orders.common import OptionInstruction, OrderType, OrderStrategyType

    return (__base_builder()
            .set_order_type(OrderType.LIMIT)
            .set_price(price)
            .set_order_strategy_type(OrderStrategyType.SINGLE)
            .add_option_leg(OptionInstruction.BUY_TO_OPEN, symbol, quantity)
            )


# Sell to Open

def option_sell_to_open_market(symbol, quantity):
    '''
    Returns a pre-filled :class:`~schwab.orders.generic.OrderBuilder` for a
    sell-to-open market order.
    '''
    from schwab.orders.common import OptionInstruction, OrderType, OrderStrategyType

    return (__base_builder()
            .set_order_type(OrderType.MARKET)
            .set_order_strategy_type(OrderStrategyType.SINGLE)
            .add_option_leg(OptionInstruction.SELL_TO_OPEN, symbol, quantity))


def option_sell_to_open_limit(symbol, quantity, price):
    '''
    Returns a pre-filled :class:`~schwab.orders.generic.OrderBuilder` for a
    sell-to-open limit order.
    '''
    from schwab.orders.common import OptionInstruction, OrderType, OrderStrategyType

    return (__base_builder()
            .set_order_type(OrderType.LIMIT)
            .set_price(price)
            .set_order_strategy_type(OrderStrategyType.SINGLE)
            .add_option_leg(OptionInstruction.SELL_TO_OPEN, symbol, quantity)
            )


# Buy to Close


def option_buy_to_close_market(symbol, quantity):
    '''
    Returns a pre-filled :class:`~schwab.orders.generic.OrderBuilder` for a
    buy-to-close market order.
    '''
    from schwab.orders.common import OptionInstruction, OrderType, OrderStrategyType

    return (__base_builder()
            .set_order_type(OrderType.MARKET)
            .set_order_strategy_type(OrderStrategyType.SINGLE)
            .add_option_leg(OptionInstruction.BUY_TO_CLOSE, symbol, quantity))


def option_buy_to_close_limit(symbol, quantity, price):
    '''
    Returns a pre-filled :class:`~schwab.orders.generic.OrderBuilder` for a
    buy-to-close limit order.
    '''
    from schwab.orders.common import OptionInstruction, OrderType, OrderStrategyType

    return (__base_builder()
            .set_order_type(OrderType.LIMIT)
            .set_price(price)
            .set_order_strategy_type(OrderStrategyType.SINGLE)
            .add_option_leg(OptionInstruction.BUY_TO_CLOSE, symbol, quantity)
            )


# Sell to Close


def option_sell_to_close_market(symbol, quantity):
    '''
    Returns a pre-filled :class:`~schwab.orders.generic.OrderBuilder` for a
    sell-to-close market order.
    '''
    from schwab.orders.common import OptionInstruction, OrderType, OrderStrategyType

    return (__base_builder()
            .set_order_type(OrderType.MARKET)
            .set_order_strategy_type(OrderStrategyType.SINGLE)
            .add_option_leg(OptionInstruction.SELL_TO_CLOSE, symbol, quantity))


def option_sell_to_close_limit(symbol, quantity, price):
    '''
    Returns a pre-filled :class:`~schwab.orders.generic.OrderBuilder` for a
    sell-to-close limit order.
    '''
    from schwab.orders.common import OptionInstruction, OrderType, OrderStrategyType

    return (__base_builder()
            .set_order_type(OrderType.LIMIT)
            .set_price(price)
            .set_order_strategy_type(OrderStrategyType.SINGLE)
            .add_option_leg(OptionInstruction.SELL_TO_CLOSE, symbol, quantity)
            )


################################################################################
# Verticals

# Bull Call

def bull_call_vertical_open(
        long_call_symbol, short_call_symbol, quantity, net_debit):
    '''
    Returns a pre-filled :class:`~schwab.orders.generic.OrderBuilder` that opens a
    bull call vertical position. See :ref:`vertical_spreads` for details.
    '''
    from schwab.orders.common import OptionInstruction, OrderType, OrderStrategyType
    from schwab.orders.common import ComplexOrderStrategyType

    return (__base_builder()
            .set_order_type(OrderType.NET_DEBIT)
            .set_complex_order_strategy_type(ComplexOrderStrategyType.VERTICAL)
            .set_price(net_debit)
            .set_quantity(quantity)
            .set_order_strategy_type(OrderStrategyType.SINGLE)
            .add_option_leg(
                OptionInstruction.BUY_TO_OPEN, long_call_symbol, quantity)
            .add_option_leg(
                OptionInstruction.SELL_TO_OPEN, short_call_symbol, quantity))


def bull_call_vertical_close(
        long_call_symbol, short_call_symbol, quantity, net_credit):
    '''
    Returns a pre-filled :class:`~schwab.orders.generic.OrderBuilder` that closes a
    bull call vertical position. See :ref:`vertical_spreads` for details.
    '''
    from schwab.orders.common import OptionInstruction, OrderType, OrderStrategyType
    from schwab.orders.common import ComplexOrderStrategyType

    return (__base_builder()
            .set_order_type(OrderType.NET_CREDIT)
            .set_complex_order_strategy_type(ComplexOrderStrategyType.VERTICAL)
            .set_price(net_credit)
            .set_quantity(quantity)
            .set_order_strategy_type(OrderStrategyType.SINGLE)
            .add_option_leg(
                OptionInstruction.SELL_TO_CLOSE, long_call_symbol, quantity)
            .add_option_leg(
                OptionInstruction.BUY_TO_CLOSE, short_call_symbol, quantity))


# Bear Call

def bear_call_vertical_open(
        short_call_symbol, long_call_symbol, quantity, net_credit):
    '''
    Returns a pre-filled :class:`~schwab.orders.generic.OrderBuilder` that opens a
    bear call vertical position. See :ref:`vertical_spreads` for details.
    '''
    from schwab.orders.common import OptionInstruction, OrderType, OrderStrategyType
    from schwab.orders.common import ComplexOrderStrategyType

    return (__base_builder()
            .set_order_type(OrderType.NET_CREDIT)
            .set_complex_order_strategy_type(ComplexOrderStrategyType.VERTICAL)
            .set_price(net_credit)
            .set_quantity(quantity)
            .set_order_strategy_type(OrderStrategyType.SINGLE)
            .add_option_leg(
                OptionInstruction.SELL_TO_OPEN, short_call_symbol, quantity)
            .add_option_leg(
                OptionInstruction.BUY_TO_OPEN, long_call_symbol, quantity))


def bear_call_vertical_close(
        short_call_symbol, long_call_symbol, quantity, net_debit):
    '''
    Returns a pre-filled :class:`~schwab.orders.generic.OrderBuilder` that closes a
    bear call vertical position. See :ref:`vertical_spreads` for details.
    '''
    from schwab.orders.common import OptionInstruction, OrderType, OrderStrategyType
    from schwab.orders.common import ComplexOrderStrategyType

    return (__base_builder()
            .set_order_type(OrderType.NET_DEBIT)
            .set_complex_order_strategy_type(ComplexOrderStrategyType.VERTICAL)
            .set_price(net_debit)
            .set_quantity(quantity)
            .set_order_strategy_type(OrderStrategyType.SINGLE)
            .add_option_leg(
                OptionInstruction.BUY_TO_CLOSE, short_call_symbol, quantity)
            .add_option_leg(
                OptionInstruction.SELL_TO_CLOSE, long_call_symbol, quantity))


# Bull Put

def bull_put_vertical_open(
        long_put_symbol, short_put_symbol, quantity, net_credit):
    '''
    Returns a pre-filled :class:`~schwab.orders.generic.OrderBuilder` that opens a
    bull put vertical position. See :ref:`vertical_spreads` for details.
    '''
    from schwab.orders.common import OptionInstruction, OrderType, OrderStrategyType
    from schwab.orders.common import ComplexOrderStrategyType

    return (__base_builder()
            .set_order_type(OrderType.NET_CREDIT)
            .set_complex_order_strategy_type(ComplexOrderStrategyType.VERTICAL)
            .set_price(net_credit)
            .set_quantity(quantity)
            .set_order_strategy_type(OrderStrategyType.SINGLE)
            .add_option_leg(
                OptionInstruction.BUY_TO_OPEN, long_put_symbol, quantity)
            .add_option_leg(
                OptionInstruction.SELL_TO_OPEN, short_put_symbol, quantity))


def bull_put_vertical_close(
        long_put_symbol, short_put_symbol, quantity, net_debit):
    '''
    Returns a pre-filled :class:`~schwab.orders.generic.OrderBuilder` that closes a
    bull put vertical position. See :ref:`vertical_spreads` for details.
    '''
    from schwab.orders.common import OptionInstruction, OrderType, OrderStrategyType
    from schwab.orders.common import ComplexOrderStrategyType

    return (__base_builder()
            .set_order_type(OrderType.NET_DEBIT)
            .set_complex_order_strategy_type(ComplexOrderStrategyType.VERTICAL)
            .set_price(net_debit)
            .set_quantity(quantity)
            .set_order_strategy_type(OrderStrategyType.SINGLE)
            .add_option_leg(
                OptionInstruction.SELL_TO_CLOSE, long_put_symbol, quantity)
            .add_option_leg(
                OptionInstruction.BUY_TO_CLOSE, short_put_symbol, quantity))


# Bear Put

def bear_put_vertical_open(
        short_put_symbol, long_put_symbol, quantity, net_debit):
    '''
    Returns a pre-filled :class:`~schwab.orders.generic.OrderBuilder` that opens a
    bear put vertical position. See :ref:`vertical_spreads` for details.
    '''
    from schwab.orders.common import OptionInstruction, OrderType, OrderStrategyType
    from schwab.orders.common import ComplexOrderStrategyType

    return (__base_builder()
            .set_order_type(OrderType.NET_DEBIT)
            .set_complex_order_strategy_type(ComplexOrderStrategyType.VERTICAL)
            .set_price(net_debit)
            .set_quantity(quantity)
            .set_order_strategy_type(OrderStrategyType.SINGLE)
            .add_option_leg(
                OptionInstruction.SELL_TO_OPEN, short_put_symbol, quantity)
            .add_option_leg(
                OptionInstruction.BUY_TO_OPEN, long_put_symbol, quantity))


def bear_put_vertical_close(
        short_put_symbol, long_put_symbol, quantity, net_credit):
    '''
    Returns a pre-filled :class:`~schwab.orders.generic.OrderBuilder` that closes a
    bear put vertical position. See :ref:`vertical_spreads` for details.
    '''
    from schwab.orders.common import OptionInstruction, OrderType, OrderStrategyType
    from schwab.orders.common import ComplexOrderStrategyType

    return (__base_builder()
            .set_order_type(OrderType.NET_CREDIT)
            .set_complex_order_strategy_type(ComplexOrderStrategyType.VERTICAL)
            .set_price(net_credit)
            .set_quantity(quantity)
            .set_order_strategy_type(OrderStrategyType.SINGLE)
            .add_option_leg(
                OptionInstruction.BUY_TO_CLOSE, short_put_symbol, quantity)
            .add_option_leg(
                OptionInstruction.SELL_TO_CLOSE, long_put_symbol, quantity))
