package com.arturgpt.skufaddon.api.machine;

/**
 * Implemented by a machine that provides a "sauna" environment to nearby receivers.
 * Conceptually mirrors GregTech's cleanroom provider, but instead of cleanliness it
 * exposes a heat state that is used to relax (lower) the tilt level of tilt machines.
 */
public interface ISaunaProvider {

    /**
     * @return whether the sauna is currently hot enough to affect its receivers
     */
    boolean isHot();
}
