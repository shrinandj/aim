from typing import Iterable, Tuple
from collections import namedtuple

from aim.storage.treeutils import encode_tree

from aim.sdk.objects import Image
from aim.sdk.sequence_collection import SequenceCollection
from aim.sdk.sequence import Sequence
from aim.sdk.run import Run

from aim.web.api.runs.utils import get_run_props, collect_run_streamable_data


IndexRange = namedtuple('IndexRange', ['start', 'stop'])


def sliced_img_record(values: Iterable[Image], _slice: slice) -> Iterable[Image]:
    yield from zip(range(_slice.start, _slice.stop, _slice.step), values[_slice])


def img_record_to_encodable(image_record):
    img_list = []
    for idx, img in image_record:
        img_dump = img.json()
        img_dump['blob_uri'] = ''  # TODO [AT]: Integrate URI service here
        img_dump['index'] = idx
        img_list.append(img_dump)
    return img_list


def get_record_and_index_range(traces: SequenceCollection, trace_cache: dict) -> Tuple[IndexRange, IndexRange]:
    rec_start = None
    rec_stop = -1
    idx_start = 0  # record inner indexing is always sequential
    idx_stop = -1
    for run_trace_collection in traces.iter_runs():
        run = run_trace_collection.run
        run_traces = []
        for trace in run_trace_collection.iter():
            run_traces.append(trace)
            rec_start = min(trace.first_step(), rec_start) if rec_start else trace.first_step()
            rec_stop = max(trace.last_step(), rec_stop)
            idx_stop = max(trace.record_length(), idx_stop)
        trace_cache[run.hashname] = {
            'run': run,
            'traces': run_traces
        }
    return IndexRange(rec_start, rec_stop), IndexRange(idx_start, idx_stop)


def get_trace_info(trace: Sequence, rec_slice: slice, idx_slice: slice) -> dict:
    steps = []
    values = []
    steps_vals = trace.values.items_slice(_slice=rec_slice)
    for step, val in steps_vals:
        steps.append(step)
        values.append(img_record_to_encodable(sliced_img_record(val, idx_slice)))

    return {
        'trace_name': trace.name,
        'context': trace.context.to_dict(),
        'record_range': [rec_slice.start, rec_slice.stop],
        'index_range': [idx_slice.start, idx_slice.stop],
        'record_slice': [rec_slice.start, rec_slice.stop, rec_slice.step],
        'index_slice': [idx_slice.start, idx_slice.stop, idx_slice.step],
        'values': values,
        'iters': steps,
        'epochs': list(trace.epochs.values_slice(_slice=rec_slice)),
        'timestamps': list(trace.timestamps.values_slice(_slice=rec_slice)),
    }


def image_search_result_streamer(traces: SequenceCollection, rec_slice: slice, idx_slice: slice):
    record_range_missing = rec_slice.start is None or rec_slice.stop is None
    index_range_missing = idx_slice.start is None or idx_slice.stop is None
    run_traces = {}
    if record_range_missing or index_range_missing:
        record_range, index_range = get_record_and_index_range(traces, trace_cache=run_traces)

    rec_start = rec_slice.start or record_range.start
    rec_stop = rec_slice.stop or record_range.stop
    rec_step = rec_slice.step or ((rec_stop - rec_start) // 50 or 1)

    idx_start = idx_slice.start or index_range.start
    idx_stop = idx_slice.stop or index_range.stop
    idx_step = idx_slice.step or ((idx_stop - idx_start) // 5 or 1)

    rec_slice = slice(rec_start, rec_stop, rec_step)
    idx_slice = slice(idx_start, idx_stop, idx_step)

    def pack_run_data(run_: Run, traces_: list):
        run_dict = {
            run_.hashname: {
                'params': run_.get(...),
                'traces': traces_,
                'props': get_run_props(run_)
            }
        }
        encoded_tree = encode_tree(run_dict)
        return collect_run_streamable_data(encoded_tree)

    if run_traces:
        for run_info in run_traces.values():
            traces_list = []
            for trace in run_info['traces']:
                traces_list.append(get_trace_info(trace, rec_slice, idx_slice))
            yield pack_run_data(run_info['run'], traces_list)
    else:
        for run_trace_collection in traces.iter_runs():
            traces_list = []
            for trace in run_trace_collection.iter():
                traces_list.append(get_trace_info(trace, rec_slice, idx_slice))
            yield pack_run_data(run_trace_collection.run, traces_list)