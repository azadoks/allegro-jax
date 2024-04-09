import e3nn_jax as e3nn
import flax
import haiku as hk
import jax
import jax.numpy as jnp
import jraph

from allegro_jax import Allegro, AllegroHaiku


def dummy_graph():
    return jraph.GraphsTuple(
        nodes={
            "positions": jnp.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
            "species": jnp.array([0, 1]),
        },
        edges=None,
        globals=None,
        senders=jnp.array([0, 1]),
        receivers=jnp.array([1, 0]),
        n_node=jnp.array([2]),
        n_edge=jnp.array([2]),
    )


class FlaxModel(flax.linen.Module):
    @flax.linen.compact
    def __call__(self, graph):
        node_attrs = jax.nn.one_hot(graph.nodes["species"], 2)
        vectors = e3nn.IrrepsArray(
            "1o",
            graph.nodes["positions"][graph.receivers]
            - graph.nodes["positions"][graph.senders],
        )
        return Allegro(avg_num_neighbors=3, radial_cutoff=2.0)(
            node_attrs, vectors, graph.senders, graph.receivers
        )


def test_allegro_flax():
    graph = dummy_graph()

    model = FlaxModel()
    w = model.init(jax.random.PRNGKey(0), graph)

    apply = jax.jit(model.apply)
    apply(w, graph)
    apply(w, graph)


def test_allegro_haiku():
    graph = dummy_graph()

    @hk.without_apply_rng
    @hk.transform
    def model(graph):
        node_attrs = jax.nn.one_hot(graph.nodes["species"], 2)
        vectors = e3nn.IrrepsArray(
            "1o",
            graph.nodes["positions"][graph.receivers]
            - graph.nodes["positions"][graph.senders],
        )
        return AllegroHaiku(avg_num_neighbors=3, radial_cutoff=2.0)(
            node_attrs, vectors, graph.senders, graph.receivers
        )

    w = model.init(jax.random.PRNGKey(0), graph)

    apply = jax.jit(model.apply)
    apply(w, graph)
    apply(w, graph)
