package com.arturgpt.skufaddon.client.render;

import net.minecraft.client.renderer.GameRenderer;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.world.inventory.InventoryMenu;

import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.VertexFormat;

/**
 * Custom {@link RenderType} for the Tilt machine overheat glow. It re-draws the machine's own
 * textured model quads as a translucent, full-bright (emissive) decal layered exactly on the block
 * surface, so the texture itself appears to glow red instead of a solid box around the block.
 */
public class SkufOverheatRenderType extends RenderType {

    private SkufOverheatRenderType(String name, VertexFormat format, VertexFormat.Mode mode, int bufferSize,
                                   boolean affectsCrumbling, boolean sortOnUpload,
                                   Runnable setupState, Runnable clearState) {
        super(name, format, mode, bufferSize, affectsCrumbling, sortOnUpload, setupState, clearState);
    }

    public static final RenderType OVERHEAT_GLOW = create(
            "skufaddon_overheat_glow",
            DefaultVertexFormat.BLOCK,
            VertexFormat.Mode.QUADS,
            256,
            false,
            true,
            RenderType.CompositeState.builder()
                    .setShaderState(new ShaderStateShard(GameRenderer::getRendertypeTranslucentShader))
                    .setTextureState(new TextureStateShard(InventoryMenu.BLOCK_ATLAS, false, false))
                    .setTransparencyState(TRANSLUCENT_TRANSPARENCY)
                    .setCullState(NO_CULL)
                    .setLightmapState(LIGHTMAP)
                    .setLayeringState(POLYGON_OFFSET_LAYERING)
                    .setDepthTestState(LEQUAL_DEPTH_TEST)
                    .setWriteMaskState(COLOR_WRITE)
                    .createCompositeState(false));
}
