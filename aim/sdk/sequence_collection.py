from abc import abstractmethod
from typing import Iterator
from typing import TYPE_CHECKING
import logging

from aim.sdk.sequence import Sequence
from aim.sdk.query_utils import RunView, SequenceView
from aim.storage.query import RestrictedPythonQuery


if TYPE_CHECKING:
    from aim.sdk.run import Run
    from aim.sdk.repo import Repo
    from pandas import DataFrame

logger = logging.getLogger(__name__)


class SequenceCollection:
    """Abstract interface for collection of tracked series/sequences.

    Typically represents sequences of a same run or sequences matching given query expression.
    """

    # TODO [AT]: move to a separate mixin class
    def dataframe(
        self,
        only_last: bool = False,
        include_run=True,
        include_name=True,
        include_context=True
    ) -> 'DataFrame':
        dfs = [
            metric.dataframe(include_run=include_run,
                             include_name=include_name,
                             include_context=include_context,
                             only_last=only_last)
            for metric in self
        ]
        if not dfs:
            return None
        import pandas as pd
        return pd.concat(dfs)

    def __iter__(self) -> Iterator[Sequence]:
        return self.iter()

    @abstractmethod
    def iter(self) -> Iterator[Sequence]:
        """Get Sequence iterator for collection's sequences.

        Yields:
            Next sequence object based on implementation.
        """
        ...

    @abstractmethod
    def iter_runs(self) -> Iterator['SequenceCollection']:
        """Get SequenceCollection iterator for collection's runs.

        Yields:
            Next run's SequenceCollection based on implementation.
        """
        ...


class SingleRunSequenceCollection(SequenceCollection):
    """Implementation of SequenceCollection interface for a single Run.

    Method `iter()` returns Sequence iterator which yields Sequence matching query from run's sequences.
    Method `iter_runs()` raises StopIteration, since the collection is bound to a single Run.

    Args:
         run (:obj:`Run`): Run object for which sequences are queried.
         seq_cls (:obj:`type`): The collection's sequence class. Sequences not matching to seq_cls.allowed_dtypes
            will be skipped. `Sequence` by default, meaning all sequences will match.
         query (:obj:`str`, optional): Query expression. If specified, method `iter()` will return iterator for
            sequences matching the query. If not, method `iter()` will return iterator for run's all sequences.
    """
    def __init__(
        self,
        run: 'Run',
        seq_cls=Sequence,
        query: str = ''
    ):
        self.run: 'Run' = run
        self.seq_cls = seq_cls
        if query:
            self.query = RestrictedPythonQuery(query)
        else:
            self.query = None

    def iter_runs(self) -> Iterator['SequenceCollection']:
        """"""
        logger.warning('Run is already bound to the Collection')
        raise StopIteration

    def iter(
        self
    ) -> Iterator[Sequence]:
        """"""
        allowed_dtypes = self.seq_cls.allowed_dtypes()
        seq_var = self.seq_cls.sequence_name()
        for seq_name, ctx, run in self.run.iter_sequence_info_by_type(allowed_dtypes):
            if not self.query:
                match = True
            else:
                run_view = RunView(run)
                seq_view = SequenceView(seq_name, ctx.to_dict(), run_view)
                match = self.query.check(**{'run': run_view, seq_var: seq_view})
            if not match:
                continue
            yield self.seq_cls(seq_name, ctx, run)


class QuerySequenceCollection(SequenceCollection):
    """Implementation of SequenceCollection interface for repository's sequences matching given query.

    Method `iter()` returns Sequence iterator, which yields Sequence matching query from currently
    iterated run's sequences. Once there are no sequences left in current run, repository's next run is considered.
    Method `iter_runs()` returns SequenceCollection iterator for repository's runs.

    Args:
         repo (:obj:`Repo`): Aim repository object.
         seq_cls (:obj:`type`): The collection's sequence class. Sequences not matching to seq_cls.allowed_dtypes
            will be skipped. `Sequence` by default, meaning all sequences will match.
         query (:obj:`str`, optional): Query expression. If specified, method `iter()` will skip sequences not matching
            the query. If not, method `iter()` will return iterator for all sequences in repository
            (that's a lot of sequences!).
    """

    def __init__(
        self,
        repo: 'Repo',
        seq_cls=Sequence,
        query: str = ''
    ):
        self.repo: 'Repo' = repo
        self.seq_cls = seq_cls
        self.query = query

    def iter_runs(self) -> Iterator['SequenceCollection']:
        """"""
        for run in self.repo.iter_runs():
            yield SingleRunSequenceCollection(run, self.seq_cls, self.query)

    def iter(self) -> Iterator[Sequence]:
        """"""
        for run_seqs in self.iter_runs():
            yield from run_seqs


class QueryRunSequenceCollection(SequenceCollection):
    """Implementation of SequenceCollection interface for repository's runs matching given query.

    Method `iter()` returns Sequence iterator which yields Sequence for current run's all sequences.
    Method `iter_runs()` returns SequenceCollection iterator from repository's runs matching given query.

    Args:
         repo (:obj:`Repo`): Aim repository object.
         seq_cls (:obj:`type`): The collection's sequence class. Sequences not matching to seq_cls.allowed_dtypes
            will be skipped. `Sequence` by default, meaning all sequences will match.
         query (:obj:`str`, optional): Query expression. If specified, method `iter_runs()` will skip runs not matching
            the query. If not, method `iter_run()` will return SequenceCollection iterator for all runs in repository.
    """

    def __init__(
        self,
        repo: 'Repo',
        seq_cls=Sequence,
        query: str = '',
        paginated: bool = False,
        offset: str = None
    ):
        self.repo: 'Repo' = repo
        self.seq_cls = seq_cls
        self.query = query
        self.paginated = paginated
        self.offset = offset
        if query:
            self.query = RestrictedPythonQuery(query)

    def iter(self) -> Iterator[Sequence]:
        """"""
        for run_seq in self.iter_runs():
            yield from run_seq

    def iter_runs(self) -> Iterator['SequenceCollection']:
        """"""
        if self.paginated:
            runs_iterator = self.repo.iter_runs_from_cache(offset=self.offset)
        else:
            runs_iterator = self.repo.iter_runs()
        for run in runs_iterator:
            if not self.query:
                match = True
            else:
                run_view = RunView(run)
                match = self.query.check(run=run_view)
            if not match:
                continue
            yield SingleRunSequenceCollection(run, self.seq_cls)